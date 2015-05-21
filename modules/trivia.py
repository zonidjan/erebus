# Erebus IRC bot - Author: Erebus Team
# trivia module
# This file is released into the public domain; see http://unlicense.org/

#TODO:
#	timers (stop game/skip question/hinting)
#	bonus points
#	ability to REDUCE users points
#	dynamic questions
#	v2
#		team play
#		statistics

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
	del state
	return lib.modstop(*args, **kwargs)

# module code
import json, random, threading, re

def findnth(haystack, needle, n): #http://stackoverflow.com/a/1884151
	parts = haystack.split(needle, n+1)
	if len(parts)<=n+1:
		return -1
	return len(haystack)-len(parts[-1])-len(needle)

class TriviaState(object):
	def __init__(self, questionfile):
		self.questionfile = questionfile
		self.db = json.load(open(questionfile, "r"))
		self.chan = self.db['chan']
		self.curq = None
		self.nextq = None
		self.steptimer = None
		self.hintstr = None
		self.hintanswer = None
		self.revealpossibilities = None

	def __del__(self):
		if threading is not None and threading._Timer is not None and isinstance(self.steptimer, threading._Timer):
			self.steptimer.cancel()
		if json is not None and json.dump is not None:
			json.dump(self.db, open(self.questionfile, "w"), indent=4, separators=(',',': '))

	def nexthint(self, hintnum):
		if self.hintanswer is None:
			if isinstance(self.curq['answer'], basestring): self.hintanswer = self.curq['answer']
			else: self.hintanswer = random.choice(self.curq['answer'])
		answer = self.hintanswer

		if self.hintstr is None or self.revealpossibilities is None:
			self.hintstr = list(re.sub(r'[a-zA-Z0-9]', '*', answer))
			self.revealpossibilities = range(''.join(self.hintstr).count('*'))

		reveal = int(len(self.hintstr) * (7/24.0))
		for i in range(reveal):
			revealcount = random.choice(self.revealpossibilities)
			revealloc = findnth(''.join(self.hintstr), '*', revealcount)
			self.revealpossibilities.remove(revealcount)
			self.hintstr[revealloc] = answer[revealloc]
		self.parent.channel(self.chan).bot.msg(self.chan, "Here's a hint: %s" % (''.join(self.hintstr)))

		if hintnum < 3:
			self.steptimer = threading.Timer(15.0, self.nexthint, args=[hintnum+1])
			self.steptimer.start()
		else:
			self.steptimer = threading.Timer(15.0, self.nextquestion)
			self.steptimer.start()

	def nextquestion(self):
		if isinstance(self.steptimer, threading._Timer):
			self.steptimer.cancel()
		self.hintstr = None
		self.hintanswer = None
		self.revealpossibilities = None


		if state.nextq is not None:
			nextq = state.nextq
			self.curq = nextq
			state.nextq = None
		else:
			nextq = random.choice(self.db['questions'])
			self.curq = nextq

		qtext = "\00300,01Next up: "
		qary = nextq['question'].split(None)
		for qword in qary:
			qtext += "\00300,01"+qword+"\00301,01"+chr(random.randrange(32,126))
		self.parent.channel(self.chan).bot.msg(self.chan, qtext)

		self.steptimer = threading.Timer(15.0, self.nexthint, args=[1])
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

		oldrank = self.db['users'][user]['rank']
		while oldrank != 0:
			nextperson = self.db['ranks'][oldrank-1]
			if self.db['users'][user]['points'] > self.db['users'][nextperson]['points']:
				self.db['ranks'][oldrank-1] = user
				self.db['users'][user]['rank'] = oldrank-1
				self.db['ranks'][oldrank] = nextperson
				self.db['users'][nextperson]['rank'] = oldrank
				oldrank = oldrank-1
			else:
				break
		return self.db['users'][user]['points']

	def points(self, user):
		user = str(user).lower()
		if user in self.db['users']:
			return self.db['users'][user]['points']
		else:
			return 0

	def rank(self, user):
		user = str(user).lower()
		return self.db['users'][user]['rank']+1
	
	def targetuser(self, user):
		user = str(user).lower()
		rank = self.db['users'][user]['rank']
		if rank == 0:
			return "you're in the lead!"
		else:
			return self.db['ranks'][rank-1]
	def targetpoints(self, user):
		user = str(user).lower()
		rank = self.db['users'][user]['rank']
		if rank == 0:
			return "N/A"
		else:
			return self.db['users'][self.db['ranks'][rank-1]]['points']

state = TriviaState("/home/jrunyon/erebus/modules/trivia.json") #TODO get path from config

@lib.hookchan(state.db['chan'])
def trivia_checkanswer(bot, user, chan, *args):
	line = ' '.join([str(arg) for arg in args])
	if state.checkanswer(line):
		bot.msg(chan, "\00308%s\003 has it! The answer was \00308%s\003. Current points: %d. Rank: %d. Target: %s (%s)." % (user, line, state.addpoint(user), state.rank(user), state.targetuser(user), state.targetpoints(user)))
		state.nextquestion()

@lib.hook('points')
def cmd_points(bot, user, chan, realtarget, *args):
	if chan == realtarget: replyto = chan
	else: replyto = user

	if len(args) != 0: who = args[0]
	else: who = user

	bot.msg(replyto, "%s has %d points." % (who, state.points(who)))

@lib.hook('give', clevel=lib.OP)
@lib.argsGE(1)
def cmd_give(bot, user, chan, realtarget, *args):
	whoto = args[0]
	if len(args) > 1:
		numpoints = int(args[1])
	else:
		numpoints = 1
	balance = state.addpoint(whoto, numpoints)
	bot.msg(chan, "%s gave %s %d points. New balance: %d" % (user, whoto, numpoints, balance))

@lib.hook('setnext', clevel=lib.OP)
@lib.argsGE(1)
def cmd_setnext(bot, user, chan, realtarget, *args):
	line = ' '.join([str(arg) for arg in args])
	linepieces = line.split('*')
	question = linepieces[0].strip()
	answer = linepieces[1].strip()
	state.nextq = {'question':question,'answer':answer}
	bot.msg(user, "Done.")

@lib.hook('skip', clevel=lib.KNOWN)
def cmd_skip(bot, user, chan, realtarget, *args):
	state.nextquestion()

@lib.hook('start')
def cmd_start(bot, user, chan, realtarget, *args):
	if chan == realtarget: replyto = chan
	else: replyto = user

	if state.curq is None:
		state.nextquestion()
	else:
		bot.msg(replyto, "Game is already started!")

@lib.hook('stop', clevel=lib.KNOWN)
def cmd_stop(bot, user, chan, realtarget, *args):
	if chan == realtarget: replyto = chan
	else: replyto = user

	if state.curq is not None:
		state.curq = None
		if isinstance(state.steptimer, threading._Timer):
			state.steptimer.cancel()
		bot.msg(chan, "Game ended by %s" % (user))
	else:
		bot.msg(replyto, "Game isn't running.")

@lib.hook('rank')
def cmd_rank(bot, user, chan, realtarget, *args):
	if chan == realtarget: replyto = chan
	else: replyto = user

	if len(args) != 0: who = args[0]
	else: who = user

	bot.msg(replyto, "%s is in %d place." % (who, state.rank(who)))
