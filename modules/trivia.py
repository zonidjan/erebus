# Erebus IRC bot - Author: Erebus Team
# trivia module
# This file is released into the public domain; see http://unlicense.org/

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
	global state
	stop()
	state.closeshop()
	del state
	return lib.modstop(*args, **kwargs)

# module code
import json, random, threading, re, time, datetime

try:
	import twitter 
except: pass # doesn't matter if we don't have twitter, updating the status just will fall through the try-except if so...

def findnth(haystack, needle, n): #http://stackoverflow.com/a/1884151
	parts = haystack.split(needle, n+1)
	if len(parts)<=n+1:
		return -1
	return len(haystack)-len(parts[-1])-len(needle)

class TriviaState(object):
	def __init__(self, questionfile, parent=None, pointvote=False):
		self.parent = parent
		self.questionfile = self.getbot().parent.cfg.get('trivia', 'jsonpath')
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
		self.missedquestions = 0

		if 'starttime' not in self.db or self.db['starttime'] is None:
			self.db['starttime'] = time.time()

		if pointvote:
			self.getchan().msg("Vote for the next round target points! Options: %s. Vote using !vote <choice>" % (', '.join([str(x) for x in self.db['targetoptions']])))
			self.getchan().msg("You have %s seconds." % (self.db['votetimer']))
			self.voteamounts = dict([(x, 0) for x in self.db['targetoptions']]) # make a dict {pointsoptionA: 0, pointsoptionB: 0, ...}
			self.pointvote = threading.Timer(self.db['votetimer'], self.endPointVote)
			self.pointvote.start()
		else:
			self.pointvote = None

	def __del__(self):
		self.closeshop()
	def closeshop(self):
		if threading is not None and threading._Timer is not None and isinstance(self.steptimer, threading._Timer):
			self.steptimer.cancel()
		if json is not None and json.dump is not None:
			json.dump(self.db, open(self.questionfile, "w"))#, indent=4, separators=(',', ': '))

	def getchan(self):
		return self.parent.channel(self.chan)
	def getbot(self):
		return self.getchan().bot

	def nexthint(self, hintnum):
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
		self.parent.channel(self.chan).bot.msg(self.chan, "\00304,01Here's a hint: %s" % (''.join(self.hintstr)))

		self.hintsgiven += 1

		if hintnum < self.db['hintnum']:
			self.steptimer = threading.Timer(self.db['hinttimer'], self.nexthint, args=[hintnum+1])
			self.steptimer.start()
		else:
			self.steptimer = threading.Timer(self.db['hinttimer'], self.nextquestion, args=[True])
			self.steptimer.start()

	def doGameOver(self):
		msg = self.getchan().msg
		def person(num): return self.db['users'][self.db['ranks'][num]]['realnick']
		def pts(num): return str(self.db['users'][self.db['ranks'][num]]['points'])
		winner = person(0)
		try:
			msg("\00312THE GAME IS OVER!!!")
			msg("THE WINNER IS: %s (%s)" % (person(0), pts(0)))
			msg("2ND PLACE: %s (%s)" % (person(1), pts(1)))
			msg("3RD PLACE: %s (%s)" % (person(2), pts(2)))
			[msg("%dth place: %s (%s)" % (i+1, person(i), pts(i))) for i in range(3,10)]
		except IndexError: pass
		except Exception as e: msg("DERP! %r" % (e))

		if self.db['hofpath'] is not None and self.db['hofpath'] != '':
			self.writeHof()

		self.db['users'] = {}
		self.db['ranks'] = []
		stop()
		self.closeshop()

		try:
			t = twitter.Twitter(auth=twitter.OAuth(self.getbot().parent.cfg.get('trivia', 'token'),
				self.getbot().parent.cfg.get('trivia', 'token_sec'),
				self.getbot().parent.cfg.get('trivia', 'con'),
				self.getbot().parent.cfg.get('trivia', 'con_sec')))
			t.statuses.update(status="Round is over! The winner was %s" % (winner))
		except: pass #don't care if errors happen updating twitter.

		self.__init__(self.questionfile, self.parent, True)

	def writeHof(self):
		def person(num):
			try: return self.db['users'][self.db['ranks'][num]]['realnick']
			except: return "none"
		def pts(num):
			try: return str(self.db['users'][self.db['ranks'][num]]['points'])
			except: return 0

		try:
			f = open(self.db['hofpath'], 'rb+')
			for i in range(self.db['hoflines']): #skip this many lines
				f.readline()
			insertpos = f.tell()
			fcontents = f.read()
			f.seek(insertpos)
			f.write((self.db['hofformat']+"\n") % {
				'date': time.strftime("%F", time.gmtime()),
				'duration': str(datetime.timedelta(seconds=time.time()-self.db['starttime'])),
				'targetscore': self.db['target'],
				'firstperson': person(0),
				'firstscore': pts(0),
				'secondperson': person(1),
				'secondscore': pts(1),
				'thirdperson': person(2),
				'thirdscore': pts(2),
			})
			f.write(fcontents)
			return True
		except Exception as e:
			raise e
			return False
		finally:
			f.close()

	def endPointVote(self):
		self.getchan().msg("Voting has ended!")
		votelist = sorted(self.voteamounts.items(), key=lambda item: item[1]) #sort into list of tuples: [(option, number_of_votes), ...]
		for i in range(len(votelist)-1):
			item = votelist[i]
			self.getchan().msg("%s place: %s (%s votes)" % (len(votelist)-i, item[0], item[1]))
		self.getchan().msg("Aaaaand! The next round will be to \002%s\002 points! (%s votes)" % (votelist[-1][0], votelist[-1][1]))

		self.db['target'] = votelist[-1][0]
		self.pointvote = None

		self.nextquestion() #start the game!

	def nextquestion(self, qskipped=False, iteration=0):
		if self.gameover == True:
			return self.doGameOver()
		if qskipped:
			self.getchan().msg("\00304Fail! The correct answer was: %s" % (self.hintanswer))
			self.missedquestions += 1
		else:
			self.missedquestions = 0

		if isinstance(self.steptimer, threading._Timer):
			self.steptimer.cancel()

		self.hintstr = None
		self.hintsgiven = 0
		self.revealpossibilities = None
		self.reveal = None

		if self.missedquestions > self.db['maxmissedquestions']:
			stop()
			self.getbot().msg(self.getchan(), "%d questions unanswered! Stopping the game.")

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

		qtext = "\00304,01Next up: "
		qary = nextq['question'].split(None)
		for qword in qary:
			qtext += "\00304,01"+qword+"\00301,01"+chr(random.randrange(0x61,0x7A)) #a-z
		self.getbot().msg(self.chan, qtext)

		self.curq = nextq

		if isinstance(self.curq['answer'], basestring): self.hintanswer = self.curq['answer']
		else: self.hintanswer = random.choice(self.curq['answer'])

		self.steptimer = threading.Timer(self.db['hinttimer'], self.nexthint, args=[1])
		self.steptimer.start()

	def checkanswer(self, answer):
		if self.curq is None:
			return False
		elif isinstance(self.curq['answer'], basestring):
			return answer.lower() == self.curq['answer']
		else: # assume it's a list or something.
			return answer.lower() in self.curq['answer']

	def addpoint(self, user_obj, count=1):
		user_nick = str(user_obj)
		user = user_nick.lower() # save this separately as we use both
		if user in self.db['users']:
			self.db['users'][user]['points'] += count
		else:
			self.db['users'][user] = {'points': count, 'realnick': user_nick, 'rank': len(self.db['ranks'])}
			self.db['ranks'].append(user)

		self.db['ranks'].sort(key=lambda nick: state.db['users'][nick]['points'], reverse=True) #re-sort ranks, rather than dealing with anything more efficient
		for i in range(0, len(self.db['ranks'])):
			nick = self.db['ranks'][i]
			self.db['users'][nick]['rank'] = i

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
		bot.msg(chan, "\00312%s\003 has it! The answer was \00312%s\003. New score: %d. Rank: %d. Target: %s (%s)." % (user, line, state.addpoint(user), state.rank(user), state.targetuser(user), state.targetpoints(user)))
		if state.hintsgiven == 0:
			bot.msg(chan, "\00312%s\003 got an extra point for getting it before the hints! New score: %d." % (user, state.addpoint(user)))
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
	state.nextquestion(True)

@lib.hook('start', needchan=False)
def cmd_start(bot, user, chan, realtarget, *args):
	if chan == realtarget: replyto = chan
	else: replyto = user

	if state.curq is None and state.pointvote is None:
		state.nextquestion()
	elif state.pointvote is not None:
		bot.msg(replyto, "There's a vote in progress!")
	else:
		bot.msg(replyto, "Game is already started!")

#FIXME @lib.hook('stop', clevel=lib.KNOWN, needchan=False)
@lib.hook('stop', needchan=False) #FIXME
def cmd_stop(bot, user, chan, realtarget, *args):
	if stop():
		bot.msg(state.chan, "Game stopped by %s" % (user))
	else:
		bot.msg(user, "Game isn't running.")

def stop():
	if state.curq is not None:
		state.curq = None
		try:
			state.steptimer.cancel()
		except Exception as e:
			print "!!! steptimer.cancel(): e"
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

		if state.pointvote is not None:
			state.pointvote.cancel()
			state.pointvote = None
			bot.msg(state.db['chan'], "Vote has been cancelled!")
	except Exception as e:
		print e
		bot.msg(user, "Failed to set target.")

@lib.hook('vote', needchan=False)
def cmd_vote(bot, user, chan, realtarget, *args):
	if state.pointvote is not None:
		if int(args[0]) in state.voteamounts:
			state.voteamounts[int(args[0])] += 1
			bot.msg(user, "Your vote has been recorded.")
		else:
			bot.msg(user, "Sorry - that's not an option!")
	else:
		bot.msg(user, "There's no vote in progress.")

@lib.hook('maxmissed', clevel=lib.MASTER, needchan=False)
def cmd_maxmissed(bot, user, chan, realtarget, *args):
	try:
		state.db['maxmissedquestions'] = int(args[0])
		bot.msg(state.db['chan'], "Max missed questions before round ends has been changed to %s." % (state.db['maxmissedquestions']))
	except:
		bot.msg(user, "Failed to set maxmissed.")

@lib.hook('hinttimer', clevel=lib.MASTER, needchan=False)
def cmd_hinttimer(bot, user, chan, realtarget, *args):
	try:
		state.db['hinttimer'] = float(args[0])
		bot.msg(state.db['chan'], "Time between hints has been changed to %s." % (state.db['hinttimer']))
	except:
		bot.msg(user, "Failed to set hint timer.")

@lib.hook('hintnum', clevel=lib.MASTER, needchan=False)
def cmd_hintnum(bot, user, chan, realtarget, *args):
	try:
		state.db['hintnum'] = int(args[0])
		bot.msg(state.db['chan'], "Max number of hints has been changed to %s." % (state.db['hintnum']))
	except:
		bot.msg(user, "Failed to set hintnum.")

@lib.hook('findq', clevel=lib.KNOWN, needchan=False)
def cmd_findquestion(bot, user, chan, realtarget, *args):
	matches = [str(i) for i in range(len(state.db['questions'])) if state.db['questions'][i]['question'] == ' '.join(args)] #FIXME: looser equality check
	if len(matches) > 1:
		bot.msg(user, "Multiple matches: %s" % (', '.join(matches)))
	elif len(matches) == 1:
		bot.msg(user, "One match: %s" % (matches[0]))
	else:
		bot.msg(user, "No match.")

@lib.hook('delq', clevel=lib.OP, needchan=False)
@lib.hook('deleteq', clevel=lib.OP, needchan=False)
def cmd_deletequestion(bot, user, chan, realtarget, *args):
	try:
		backup = state.db['questions'][int(args[0])]
		del state.db['questions'][int(args[0])]
		bot.msg(user, "Deleted %s*%s" % (backup['question'], backup['answer']))
	except:
		bot.msg(user, "Couldn't delete that question.")

@lib.hook('addq', clevel=lib.OP, needchan=False)
def cmd_addquestion(bot, user, chan, realtarget, *args):
	line = ' '.join([str(arg) for arg in args])
	linepieces = line.split('*')
	if len(linepieces) < 2:
		bot.msg(user, "Error: need <question>*<answer>")
		return
	question = linepieces[0].strip()
	answer = linepieces[1].strip()
	state.db['questions'].append({'question':question,'answer':answer})
	bot.msg(user, "Done. Question is #%s" % (len(state.db['questions'])-1))


@lib.hook('triviahelp', needchan=False)
def cmd_triviahelp(bot, user, chan, realtarget, *args):
	bot.msg(user,             "START")
	bot.msg(user,             "TOP10")
	bot.msg(user,             "POINTS    [<user>]")
	bot.msg(user,             "RANK      [<user>]")
	if bot.parent.channel(state.db['chan']).levelof(user.auth) >= lib.KNOWN:
		bot.msg(user,         "SKIP                        (>=KNOWN )")
		bot.msg(user,         "STOP                        (>=KNOWN )")
		bot.msg(user,         "FINDQ     <question>     (>=KNOWN )")
		if bot.parent.channel(state.db['chan']).levelof(user.auth) >= lib.OP:
			bot.msg(user,     "GIVE      <user> [<points>] (>=OP    )")
			bot.msg(user,     "SETNEXT   <q>*<a>           (>=OP    )")
			bot.msg(user,     "ADDQ      <q>*<a>           (>=OP    )")
			bot.msg(user,     "DELETEQ   <q>*<a>           (>=OP    )  [aka DELQ]")
			if bot.parent.channel(state.db['chan']).levelof(user.auth) >= lib.MASTER:
				bot.msg(user, "SETTARGET <points>          (>=MASTER)")
				bot.msg(user, "MAXMISSED <questions>       (>=MASTER)")
				bot.msg(user, "HINTTIMER <float seconds>   (>=MASTER)")
				bot.msg(user, "HINTNUM   <hints>           (>=MASTER)")

@lib.hooknum(417)
def num_417(bot, textline):
	bot.msg(state.db['chan'], "Whoops, it looks like that question didn't quite go through! (E:417). Let's try another...")
	state.nextquestion(False)


def specialQuestion(oldq):
	newq = {'question': oldq['question'], 'answer': oldq['answer']}
	qtype = oldq['question'].upper()

	if qtype == "!MONTH":
		newq['question'] = "What month is it currently (in UTC)?"
		newq['answer'] = time.strftime("%B", time.gmtime()).lower()
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
