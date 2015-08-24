# Erebus IRC bot - Author: Erebus Team
# trivia module
# This file is released into the public domain; see http://unlicense.org/

#TODO:
#	stop game after X unanswered questions
#	bonus points
#	v2
#		team play
#		statistics

HINTTIMER = 15.0
HINTNUM = 3

# module info
modinfo = {
	'author': 'Erebus Team',
	'license': 'public domain',
	'compatible': [1], # compatible module API versions
	'depends': [], # other modules required to work properly?
}

# preamble
import modlib
lib = modlib.modlib(__name__)
def modstart(parent, *args, **kwargs):
	state.parent = parent
	return lib.modstart(parent, *args, **kwargs)
def modstop(*args, **kwargs):
	stop()
	state.closeshop()
	global state
	del state
	return lib.modstop(*args, **kwargs)

# module code
import json, random, threading, re, time

def findnth(haystack, needle, n): #http://stackoverflow.com/a/1884151
	parts = haystack.split(needle, n+1)
	if len(parts)<=n+1:
		return -1
	return len(haystack)-len(parts[-1])-len(needle)

class TriviaState(object):
	def __init__(self, questionfile, parent=None):
		self.parent = parent
		self.questionfile = questionfile
		self.db = json.load(open(questionfile, "r"))
		self.chan = self.db['chan']
		self.curq = None
		self.nextq = None
		self.steptimer = None
		self.hintstr = None
		self.hintanswer = None
		self.hintsgiven = 0
		self.revealpossibilities = None
		self.gameover = False

	def __del__(self):
		self.closeshop()
	def closeshop(self):
		if threading is not None and threading._Timer is not None and isinstance(self.steptimer, threading._Timer):
			self.steptimer.cancel()
		if json is not None and json.dump is not None:
			json.dump(self.db, open(self.questionfile, "w"), indent=4, separators=(',',': '))

	def getchan(self):
		return self.parent.channel(self.chan)
	def getbot(self):
		return self.getchan().bot

	def nexthint(self, hintnum):
		if self.hintanswer is None:
			if isinstance(self.curq['answer'], basestring): self.hintanswer = self.curq['answer']
			else: self.hintanswer = random.choice(self.curq['answer'])
		answer = self.hintanswer

		if self.hintstr is None or self.revealpossibilities is None or self.reveal is None:
			self.hintstr = list(re.sub(r'[a-zA-Z0-9]', '*', answer))
			self.revealpossibilities = range(''.join(self.hintstr).count('*'))
			self.reveal = int(''.join(self.hintstr).count('*') * (7/24.0))

		for i in range(self.reveal):
			revealcount = random.choice(self.revealpossibilities)
			revealloc = findnth(''.join(self.hintstr), '*', revealcount)
			self.revealpossibilities.remove(revealcount)
			self.hintstr[revealloc] = answer[revealloc]
		self.parent.channel(self.chan).bot.msg(self.chan, "Here's a hint: %s" % (''.join(self.hintstr)))

		self.hintsgiven += 1

		if hintnum < HINTNUM:
			self.steptimer = threading.Timer(HINTTIMER, self.nexthint, args=[hintnum+1])
			self.steptimer.start()
		else:
			self.steptimer = threading.Timer(HINTTIMER, self.nextquestion, args=[True])
			self.steptimer.start()

	def doGameOver(self):
		def msg(line): self.getbot().msg(self.getchan(), line)
		def person(num): return self.db['users'][self.db['ranks'][num]]['realnick']
		def pts(num): return self.db['users'][self.db['ranks'][num]]['points']
		try:
			msg("\00312THE GAME IS OVER!!!")
			msg("THE WINNER IS: %s (%s)" % (person(0), pts(0)))
			msg("2ND PLACE: %s (%s)" % (person(1), pts(1)))
			msg("3RD PLACE: %s (%s)" % (person(2), pts(2)))
			[msg("%dth place: %s (%s)" % (i+1, person(i), pts(i))) for i in range(3,10)]
		except IndexError: pass
		except Exception as e:
			msg("DERP! %r" % (e))
		self.db['users'] = {}
		self.db['ranks'] = []
		stop()
		self.closeshop()
		self.__init__(self.questionfile, self.parent)

	def nextquestion(self, qskipped=False, iteration=0):
		if self.gameover == True:
			return self.doGameOver()
		if qskipped:
			self.getbot().msg(self.getchan(), "Fail! The correct answer was: %s" % (self.hintanswer))

		if isinstance(self.steptimer, threading._Timer):
			self.steptimer.cancel()
		self.hintstr = None
		self.hintanswer = None
		self.hintsgiven = 0
		self.revealpossibilities = None
		self.reveal = None


		if state.nextq is not None:
			nextq = state.nextq
			state.nextq = None
		else:
			nextq = random.choice(self.db['questions'])

		if nextq['question'][0] == "!":
			nextq = specialQuestion(nextq)

		if iteration < 10 and 'lastasked' in nextq and nextq['lastasked'] - time.time() < 24*60*60:
			return self.nextquestion(iteration=iteration+1) #short-circuit to pick another question
		nextq['lastasked'] = time.time()

		nextq['answer'] = nextq['answer'].lower()

		qtext = "\00300,01Next up: "
		qary = nextq['question'].split(None)
		for qword in qary:
			qtext += "\00300,01"+qword+"\00301,01"+chr(random.randrange(32,126))
		self.getbot().msg(self.chan, qtext)

		self.curq = nextq

		self.steptimer = threading.Timer(HINTTIMER, self.nexthint, args=[1])
		self.steptimer.start()

	def checkanswer(self, answer):
		if self.curq is None:
			return False
		elif isinstance(self.curq['answer'], basestring):
			return answer.lower() == self.curq['answer']
		else: # assume it's a list or something.
			return answer.lower() in self.curq['answer']

	def addpoint(self, _user, count=1):
		_user = str(_user)
		user = _user.lower()
		if user in self.db['users']:
			self.db['users'][user]['points'] += count
		else:
			self.db['users'][user] = {'points': count, 'realnick': _user, 'rank': len(self.db['ranks'])}
			self.db['ranks'].append(user)

		state.db['ranks'].sort(key=lambda nick: state.db['users'][nick]['points'], reverse=True)

		if self.db['users'][user]['points'] >= state.db['target']:
			self.gameover = True

		return self.db['users'][user]['points']

	def points(self, user):
		user = str(user).lower()
		if user in self.db['users']:
			return self.db['users'][user]['points']
		else:
			return 0

	def rank(self, user):
		user = str(user).lower()
		if user in self.db['users']:
			return self.db['users'][user]['rank']+1
		else:
			return len(self.db['users'])+1

	def targetuser(self, user):
		if len(self.db['ranks']) == 0: return "no one is ranked!"

		user = str(user).lower()
		if user in self.db['users']:
			rank = self.db['users'][user]['rank']
			if rank == 0:
				return "you're in the lead!"
			else:
				return self.db['ranks'][rank-1]
		else:
			return self.db['ranks'][-1]
	def targetpoints(self, user):
		if len(self.db['ranks']) == 0: return 0

		user = str(user).lower()
		if user in self.db['users']:
			rank = self.db['users'][user]['rank']
			if rank == 0:
				return "N/A"
			else:
				return self.db['users'][self.db['ranks'][rank-1]]['points']
		else:
			return self.db['users'][self.db['ranks'][-1]]['points']

state = TriviaState("/home/jrunyon/erebus/modules/trivia.json") #TODO get path from config

@lib.hookchan(state.db['chan'])
def trivia_checkanswer(bot, user, chan, *args):
	line = ' '.join([str(arg) for arg in args])
	if state.checkanswer(line):
		bot.msg(chan, "\00308%s\003 has it! The answer was \00308%s\003. New score: %d. Rank: %d. Target: %s (%s)." % (user, line, state.addpoint(user), state.rank(user), state.targetuser(user), state.targetpoints(user)))
		if state.hintsgiven == 0:
			bot.msg(chan, "\00308%s\003 got an extra point for getting it before the hints! New score: %d." % (user, state.addpoint(user)))
		state.nextquestion()

@lib.hook('points', needchan=False)
def cmd_points(bot, user, chan, realtarget, *args):
	if chan == realtarget: replyto = chan
	else: replyto = user

	if len(args) != 0: who = args[0]
	else: who = user

	bot.msg(replyto, "%s has %d points." % (who, state.points(who)))

@lib.hook('give', clevel=lib.OP, needchan=False)
@lib.argsGE(1)
def cmd_give(bot, user, chan, realtarget, *args):
	whoto = args[0]
	if len(args) > 1:
		numpoints = int(args[1])
	else:
		numpoints = 1
	balance = state.addpoint(whoto, numpoints)

	bot.msg(chan, "%s gave %s %d points. New balance: %d" % (user, whoto, numpoints, balance))

@lib.hook('setnext', clevel=lib.OP, needchan=False)
@lib.argsGE(1)
def cmd_setnext(bot, user, chan, realtarget, *args):
	line = ' '.join([str(arg) for arg in args])
	linepieces = line.split('*')
	if len(linepieces) < 2:
		bot.msg(user, "Error: need <question>*<answer>")
		return
	question = linepieces[0].strip()
	answer = linepieces[1].strip()
	state.nextq = {'question':question,'answer':answer}
	bot.msg(user, "Done.")

@lib.hook('skip', clevel=lib.KNOWN, needchan=False)
def cmd_skip(bot, user, chan, realtarget, *args):
	state.nextquestion()

@lib.hook('start', needchan=False)
def cmd_start(bot, user, chan, realtarget, *args):
	if chan == realtarget: replyto = chan
	else: replyto = user

	if state.curq is None:
		state.nextquestion()
	else:
		bot.msg(replyto, "Game is already started!")

@lib.hook('stop', clevel=lib.KNOWN, needchan=False)
def cmd_stop(bot, user, chan, realtarget, *args):
	if stop():
		bot.msg(state.chan, "Game stopped by %s" % (user))
	else:
		bot.msg(user, "Game isn't running.")

def stop():
	if state.curq is not None:
		state.curq = None
		if isinstance(state.steptimer, threading._Timer):
			state.steptimer.cancel()
		return True
	else:
		return False

@lib.hook('rank', needchan=False)
def cmd_rank(bot, user, chan, realtarget, *args):
	if chan == realtarget: replyto = chan
	else: replyto = user

	if len(args) != 0: who = args[0]
	else: who = user

	bot.msg(replyto, "%s is in %d place (%s points). Target is: %s (%s points)." % (who, state.rank(who), state.points(who), state.targetuser(who), state.targetpoints(who)))

@lib.hook('top10', needchan=False)
def cmd_top10(bot, user, chan, realtarget, *args):
	if len(state.db['ranks']) == 0:
		return bot.msg(state.db['chan'], "No one is ranked!")

	replylist = []
	for nick in state.db['ranks'][0:10]:
		user = state.db['users'][nick]
		replylist.append("%s (%s)" % (user['realnick'], user['points']))
	bot.msg(state.db['chan'], ', '.join(replylist))

@lib.hook('settarget', clevel=lib.MASTER, needchan=False)
def cmd_settarget(bot, user, chan, realtarget, *args):
	try:
		state.db['target'] = int(args[0])
		bot.msg(state.db['chan'], "Target has been changed to %s points!" % (state.db['target']))
	except:
		bot.msg(user, "Failed to set target.")

@lib.hook('triviahelp', needchan=False)
def cmd_triviahelp(bot, user, chan, realtarget, *args):
	bot.msg(user, "POINTS [<user>]")
	bot.msg(user, "START")
	bot.msg(user, "RANK [<user>]")
	bot.msg(user, "TOP10")

	if bot.parent.channel(state.db['chan']).levelof(user.auth) >= lib.KNOWN:
		bot.msg(user, "SKIP                      (>=KNOWN )")
		bot.msg(user, "STOP                      (>=KNOWN )")
		if bot.parent.channel(state.db['chan']).levelof(user.auth) >= lib.OP:
			bot.msg(user, "GIVE <user> [<points>]    (>=OP    )")
			bot.msg(user, "SETNEXT <q>*<a>           (>=OP    )")
			if bot.parent.channel(state.db['chan']).levelof(user.auth) >= lib.MASTER:
				bot.msg(user, "SETTARGET <points>        (>=MASTER)")


def specialQuestion(oldq):
	newq = {'question': oldq['question'], 'answer': oldq['answer']}
	qtype = oldq['question'].upper()

	if qtype == "!MONTH":
		newq['question'] = "What month is it currently (in UTC)?"
		newq['answer'] = time.strftime("%B").lower()
	elif qtype == "!MATH+":
		randnum1 = random.randrange(0, 11)
		randnum2 = random.randrange(0, 11)
		newq['question'] = "What is %d + %d?" % (randnum1, randnum2)
		newq['answer'] = spellout(randnum1+randnum2)
	return newq

def spellout(num):
	return [
		"zero", "one", "two", "three", "four", "five", "six", "seven", "eight", 
		"nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
		"sixteen", "seventeen", "eighteen", "nineteen", "twenty"
	][num]
