# Erebus IRC bot - Author: Erebus Team
# simple module example
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
	global state
	state = TriviaState("/home/jrunyon/erebus/modules/trivia.json", parent) #TODO
	return lib.modstart(parent, *args, **kwargs)
def modstop(*args, **kwargs):
	global state
	del state
	return lib.modstop(*args, **kwargs)

# module code
import json, random

class TriviaState(object):
	def __init__(self, questionfile, parent):
		self.parent = parent
		self.questionfile = questionfile
		self.db = json.load(open(questionfile, "r"))

	def __del__(self):
		json.dump(self.db, open(self.questionfile, "w"), indent=4, separators=(',',': '))

	def nextquestion(self):
		nextq = random.choice(self.db['questions'])
		self.curq = nextq
		self.parent.msg(self.chan, "Next up: %s" % (nextq['question']))

	def checkanswer(self, answer):
		if isinstance(self.curq['answer'], basestring):
			return answer.lower() == self.curq['answer']
		else: # assume it's a list or something.
			return answer.lower() in self.curq['answer']
	
	def addpoint(self, _user, count=1):
		user = _user.lower()
		if user in self.db['users']:
			self.db['users'][user]['points'] += count
		else:
			self.db['users'][user] = {'points': count, 'realnick': _user, 'rank': len(self.db['ranks'])}
			self.db['ranks']append(user)

		oldrank = self.db['users'][user]['rank']
		while oldrank != 0:
			nextperson = self.db['ranks'][oldrank-1]
			if self.db['users'][user]['points'] > self.db['users'][nextperson]['points']:
				self.db['ranks'][oldrank-1] = user
				self.db['ranks'][oldrank] = nextperson
				oldrank = oldrank-1
			else:
				break
		return self.db['users'][user]['points']

	def points(self, user):
		user = user.lower()
		if user in self.db['users']:
			return self.db['users'][user]['points']
		else:
			return 0

	def rank(self, user):
		return self.db['users'][user]['rank']
	
	def targetuser(self, user): return "TODO" #TODO
	def targetpoints(self, user): return 0 #TODO

@lib.hookchan(state.db['chan'])
def trivia_checkanswer(bot, user, chan, *args):
	global state
	line = ' '.join([str(arg) for arg in args])
	if state.checkanswer(line):
		bot.msg(chan, "\00308%s\003 has it! The answer was \00308%s\003. Current points: %d. Rank: %d. Target: %s (%d)." % (user, line, state.addpoint(user), state.rank(user), state.targetuser(user), state.targetpoints(user)))
	state.nextquestion()

@lib.hook('points')
def cmd_points(bot, user, chan, realtarget, *args):
	global state
	if chan is not None: replyto = chan
	else: replyto = user

	if len(args) != 0: who = args[0]
	else: who = user

	bot.msg(replyto, "%s has %d points." % (who, state.points(who)))

@lib.hook('give', clevel=lib.OP)
@lib.argsGE(1)
def cmd_give(bot, user, chan, realtarget, *args):
	global state
	if len(args) > 1 and args[1] != 1:
		bot.msg(user, "Giving more than one point is not yet implemented.")
		return NotImplemented

	whoto = args[0]
	balance = state.addpoint(whoto)
	bot.msg(chan, "%s gave %s %d points. New balance: %d" % (user, whoto, 1, balance))

@lib.hook('rank')
@lib.argsEQ(1)
def cmd_rank(bot, user, chan, realtarget, *args):
	global state
	if chan is not None: replyto = chan
	else: replyto = user

	bot.msg(replyto, "%s is in %d place." % (args[0], state.rank(args[0]))
