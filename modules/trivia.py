# Erebus IRC bot - Author: Erebus Team
# trivia module
# This file is released into the public domain; see http://unlicense.org/

# module info
modinfo = {
	'author': 'Erebus Team',
	'license': 'public domain',
	'compatible': [1], # compatible module API versions
	'depends': ['userinfo'], # other modules required to work properly?
}

# preamble
import modlib
lib = modlib.modlib(__name__)
def modstart(parent, *args, **kwargs):
	state.gotParent(parent)
	lib.hookchan(state.db['chan'])(trivia_checkanswer) # we need parent for this. so it goes here.
	return lib.modstart(parent, *args, **kwargs)
def modstop(*args, **kwargs):
	global state
	try:
		stop()
		state.closeshop()
		del state
	except Exception: pass
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

def person(num, throwindexerror=False):
	try:
		return state.db['users'][state.db['ranks'][num]]['realnick']
	except IndexError:
		if throwindexerror:
			raise
		else:
			return ''

def pts(num):
	try:
		return str(state.db['users'][state.db['ranks'][num]]['points'])
	except IndexError:
		return 0

def country(num, default="??"):
	return lib.mod('userinfo')._get(person(num), 'country', default=default).upper()

class MyTimer(threading._Timer):
	def __init__(self, *args, **kwargs):
		threading._Timer.__init__(self, *args, **kwargs)
		self.daemon = True

class TriviaState(object):
	def __init__(self, parent=None, pointvote=False):
		if parent is not None:
			self.gotParent(parent, pointvote)

	def gotParent(self, parent, pointvote=False):
		self.parent              = parent
		self.questionfile        = self.parent.cfg.get('trivia', 'jsonpath', default="./modules/trivia.json")
		self.db                  = json.load(open(self.questionfile, "r"))
		self.chan                = self.db['chan']
		self.curq                = None
		self.nextq               = None
		self.nextquestiontimer   = None
		self.steptimer           = None
		self.hintstr             = None
		self.hintanswer          = None
		self.hintsgiven          = 0
		self.revealpossibilities = None
		self.gameover            = False
		self.missedquestions     = 0
		self.curqid              = None
		self.lastqid             = None

		if 'lastwon' not in self.db or self.db['lastwon'] is None:
			self.db['lastwon'] = time.time()

		if pointvote:
			self.getchan().msg("Vote for the next round target points! Options: %s. Vote using !vote <choice>" % (', '.join([str(x) for x in self.db['targetoptions']])))
			self.getchan().msg("You have %s seconds." % (self.db['votetimer']))
			self.voteamounts = dict([(x, 0) for x in self.db['targetoptions']]) # make a dict {pointsoptionA: 0, pointsoptionB: 0, ...}
			self.pointvote = MyTimer(self.db['votetimer'], self.endPointVote)
			self.pointvote.start()
		else:
			self.pointvote = None

	def __del__(self):
		self.closeshop()
	def closeshop(self):
		if threading is not None and threading._Timer is not None:
			if isinstance(self.steptimer, threading._Timer):
				self.steptimer.cancel()
			if isinstance(self.nextquestiontimer, threading._Timer):
				self.nextquestiontimer.cancel()
				self.nextquestiontimer = None
		self.savedb()

	def savedb(self):
		if json is not None and json.dump is not None:
			json.dump(self.db, open(self.questionfile, "w"))#, indent=4, separators=(',', ': '))

	def getchan(self):
		return self.parent.channel(self.chan)
	def getbot(self):
		return self.getchan().bot

	def nexthint(self, hintnum):
		answer = self.hintanswer

		if self.hintstr is None or self.revealpossibilities is None or self.reveal is None:
			oldhintstr = ""
			self.hintstr = list(re.sub(r'[a-zA-Z0-9]', '*', answer))
			self.revealpossibilities = range(''.join(self.hintstr).count('*'))
			self.reveal = int(round(''.join(self.hintstr).count('*') * (7/24.0)))
		else:
			oldhintstr = ''.join(self.hintstr)

		for i in range(self.reveal):
			revealcount = random.choice(self.revealpossibilities)
			revealloc = findnth(''.join(self.hintstr), '*', revealcount)
			self.revealpossibilities.remove(revealcount)
			self.hintstr[revealloc] = answer[revealloc]
		if oldhintstr != ''.join(self.hintstr): self.getchan().fastmsg("\00304,01Here's a hint: %s" % (''.join(self.hintstr)))

		self.hintsgiven += 1

		if hintnum < self.db['hintnum']:
			self.steptimer = MyTimer(self.db['hinttimer'], self.nexthint, args=[hintnum+1])
			self.steptimer.start()
		else:
			self.steptimer = MyTimer(self.db['hinttimer'], self.nextquestion, args=[True])
			self.steptimer.start()

	def doGameOver(self):
		msg = self.getchan().msg
		winner = person(0)
		try:
			msg("\00312THE GAME IS OVER!!!")
			msg("THE WINNER IS: %s (%s)" % (person(0, True), pts(0)))
			msg("2ND PLACE: %s (%s)" % (person(1, True), pts(1)))
			msg("3RD PLACE: %s (%s)" % (person(2, True), pts(2)))
			[msg("%dth place: %s (%s)" % (i+1, person(i, True), pts(i))) for i in range(3,10)]
		except IndexError: pass
		except Exception as e:
			msg("DERP! %r" % (e))

		self.db['lastwinner'] = winner
		self.db['lastwon'] = time.time()

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

		self.__init__(self.parent, True)

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
				'duration': str(datetime.timedelta(seconds=time.time()-self.db['lastwon'])),
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
			raise e #FIXME wtf???
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

	def nextquestion(self, qskipped=False, iteration=0, skipwait=False):
		self.lastqid = self.curqid
		self.curq = None
		self.curqid = None
		if self.gameover == True:
			return self.doGameOver()
		if qskipped:
			self.getchan().fastmsg("\00304Fail! The correct answer was: %s" % (self.hintanswer))
			self.missedquestions += 1
		else:
			self.missedquestions = 0
			if 'topicformat' in self.db and self.db['topicformat'] is not None:
				self.getbot().conn.send("TOPIC %s" % (self.db['chan']))

		if isinstance(self.steptimer, threading._Timer):
			self.steptimer.cancel()
		if isinstance(self.nextquestiontimer, threading._Timer):
			self.nextquestiontimer.cancel()
			self.nextquestiontimer = None

		self.hintstr = None
		self.hintsgiven = 0
		self.revealpossibilities = None
		self.reveal = None

		if self.missedquestions > self.db['maxmissedquestions']:
			stop()
			self.getbot().msg(self.getchan(), "%d questions unanswered! Stopping the game." % (self.missedquestions))
			return

		if skipwait:
			self._nextquestion(iteration)
		else:
			self.nextquestiontimer = MyTimer(self.db['questionpause'], self._nextquestion, args=[iteration])
			self.nextquestiontimer.start()

	def _nextquestion(self, iteration):
		if self.nextq is not None:
			nextqid = None
			nextq = self.nextq
			self.nextq = None
		else:
			nextqid = random.randrange(0, len(self.db['questions']))
			nextq = self.db['questions'][nextqid]

		if nextq[0][0] == "!":
			nextqid = None
			nextq = specialQuestion(nextq)

		if len(nextq) > 2 and nextq[2] - time.time() < 7*24*60*60 and iteration < 10:
			return self._nextquestion(iteration=iteration+1) #short-circuit to pick another question
		if len(nextq) > 2:
			nextq[2] = time.time()
		else:
			nextq.append(time.time())

		if isinstance(nextq[1], basestring):
			nextq[1] = nextq[1].lower()
		else:
			nextq[1] = [s.lower() for s in nextq[1]]

		qtext = "\00312,01Next up: "
		qtext += "(%5d)" % (random.randint(0,99999))
		qary = nextq[0].split(None)
		qtext += " "
		for qword in qary:
			qtext += "\00304,01"+qword+"\00301,01"+chr(random.randrange(0x61,0x7A)) #a-z
		self.getbot().fastmsg(self.chan, qtext)

		self.curq = nextq
		self.curqid = nextqid

		if isinstance(self.curq[1], basestring): self.hintanswer = self.curq[1]
		else: self.hintanswer = random.choice(self.curq[1])

		self.steptimer = MyTimer(self.db['hinttimer'], self.nexthint, args=[1])
		self.steptimer.start()

	def checkanswer(self, answer):
		if self.curq is None:
			return False
		elif isinstance(self.curq[1], basestring):
			return answer.lower() == self.curq[1]
		else: # assume it's a list or something.
			return answer.lower() in self.curq[1]

	def addpoint(self, user_obj, count=1):
		user_nick = str(user_obj)
		user = user_nick.lower() # save this separately as we use both
		if user in self.db['users']:
			self.db['users'][user]['points'] += count
		else:
			self.db['users'][user] = {'points': count, 'realnick': user_nick, 'rank': len(self.db['ranks'])}
			self.db['ranks'].append(user)

		self.db['ranks'].sort(key=lambda nick: self.db['users'][nick]['points'], reverse=True) #re-sort ranks, rather than dealing with anything more efficient
		for i in range(0, len(self.db['ranks'])):
			nick = self.db['ranks'][i]
			self.db['users'][nick]['rank'] = i

		if self.db['users'][user]['points'] >= self.db['target']:
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

state = TriviaState()

# we have to hook this in modstart, since we don't know the channel until then.
def trivia_checkanswer(bot, user, chan, *args):
	line = ' '.join([str(arg) for arg in args])
	if state.checkanswer(line):
		state.curq = None
		if state.hintanswer.lower() == line.lower():
			bot.fastmsg(chan, "\00312%s\003 has it! The answer was \00312%s\003. New score: %d. Rank: %d. Target: %s (%s)." % (user, line, state.addpoint(user), state.rank(user), state.targetuser(user), state.targetpoints(user)))
		else:
			bot.fastmsg(chan, "\00312%s\003 has it! The answer was \00312%s\003 (hinted answer: %s). New score: %d. Rank: %d. Target: %s (%s)." % (user, line, state.hintanswer, state.addpoint(user), state.rank(user), state.targetuser(user), state.targetpoints(user)))
		if state.hintsgiven == 0:
			bot.msg(chan, "\00312%s\003 got an extra point for getting it before the hints! New score: %d." % (user, state.addpoint(user)))
		state.nextquestion()

@lib.hook(needchan=False)
@lib.help("[<user>]", "shows how many points you or someone has")
def points(bot, user, chan, realtarget, *args):
	if chan is not None and realtarget == chan.name: replyto = chan
	else: replyto = user

	if len(args) != 0: who = args[0]
	else: who = user

	bot.msg(replyto, "%s has %d points." % (who, state.points(who)))

@lib.hook(glevel=lib.STAFF, needchan=False)
@lib.help("<user> [<amount>]", "gives someone points", "defaults to 1 point")
@lib.argsGE(1)
def give(bot, user, chan, realtarget, *args):
	whoto = args[0]
	if len(args) > 1:
		numpoints = int(args[1])
	else:
		numpoints = 1
	balance = state.addpoint(whoto, numpoints)

	bot.msg(chan, "%s gave %s %d points. New balance: %d" % (user, whoto, numpoints, balance))

@lib.hook(glevel=1, needchan=False)
@lib.help("<qid>", "sets next question to one in the database")
@lib.argsEQ(1)
def setnextid(bot, user, chan, realtarget, *args):
	try:
		qid = int(args[0])
		state.nextq = state.db['questions'][qid]
		if user.glevel >= lib.STAFF:
			respstr = "Done. Next question is: %s" % (state.nextq[0])
		else:
			respstr = "Done."
		bot.msg(user, respstr)
	except Exception as e:
		bot.msg(user, "Error: %s" % (e))

@lib.hook(glevel=lib.STAFF, needchan=False)
@lib.help("<q>*<a>", "sets next question to one not in database")
@lib.argsGE(1)
def setnext(bot, user, chan, realtarget, *args):
	line = ' '.join([str(arg) for arg in args])
	linepieces = line.split('*')
	if len(linepieces) < 2:
		bot.msg(user, "Error: need <question>*<answer>")
		return
	question = linepieces[0].strip()
	answer = linepieces[1].strip()
	state.nextq = [question, answer]
	bot.msg(user, "Done.")

@lib.hook(glevel=1, needchan=False)
@lib.help(None, "skips to next question")
def skip(bot, user, chan, realtarget, *args):
	state.nextquestion(qskipped=True, skipwait=True)

@lib.hook(needchan=False)
@lib.help(None, "starts the trivia game")
def start(bot, user, chan, realtarget, *args):
	if chan is not None and realtarget == chan.name: replyto = chan
	else: replyto = user

	if chan is not None and chan.name != state.db['chan']:
		bot.msg(replyto, "That command isn't valid here.")
		return

	if state.curq is None and state.pointvote is None and state.nextquestiontimer is None:
		bot.msg(state.db['chan'], "%s has started the game!" % (user))
		state.nextquestion(skipwait=True)
	elif state.pointvote is not None:
		bot.msg(user, "There's a vote in progress!")
	else:
		bot.msg(user, "Game is already started!")

@lib.hook('stop', glevel=1, needchan=False)
@lib.help(None, "stops the trivia game")
def cmd_stop(bot, user, chan, realtarget, *args):
	if stop():
		bot.msg(state.chan, "Game stopped by %s" % (user))
	else:
		bot.msg(user, "Game isn't running.")

def stop():
	state.curq = None
	state.nextq = None
	try:
		state.steptimer.cancel()
	except Exception as e:
		print "!!! steptimer.cancel(): %s %r" % (e,e)
	state.steptimer = None
	try:
		state.nextquestiontimer.cancel()
	except Exception as e:
		print "!!! nextquestiontimer.cancel(): %s %r" % (e,e)
	state.nextquestiontimer = None
	return True

@lib.hook(needchan=False)
@lib.help("<reason>", "reports a bad question to the admins")
@lib.argsGE(1)
def badq(bot, user, chan, realtarget, *args):
	lastqid = state.lastqid
	curqid = state.curqid

	reason = ' '.join(args)
	state.db['badqs'].append([lastqid, curqid, reason])
	state.savedb()
	bot.msg(user, "Reported bad question.")

@lib.hook(glevel=lib.STAFF, needchan=False)
@lib.help(None, "shows a list of BADQ reports")
def badqs(bot, user, chan, realtarget, *args):
	if len(state.db['badqs']) == 0:
		bot.msg(user, "No reports.")

	for i in range(len(state.db['badqs'])):
		try:
			report = state.db['badqs'][i]
			bot.msg(user, "Report #%d: LastQ=%r CurQ=%r: %s" % (i, report[0], report[1], report[2]))
			try: lq = state.db['questions'][int(report[0])]
			except Exception as e: lq = (None,None)
			try: cq = state.db['questions'][int(report[1])]
			except Exception as e: cq = (None, None)
			bot.msg(user, "- Last: %s*%s" % (lq[0], lq[1]))
			bot.msg(user, "- Curr: %s*%s" % (cq[0], cq[1]))
		except Exception as e:
			bot.msg(user, "- Exception: %r" % (e))

@lib.hook(glevel=lib.STAFF, needchan=False)
@lib.hook(None, "clears list of BADQ reports")
def clearbadqs(bot, user, chan, realtarget, *args):
	state.db['badqs'] = []
	state.savedb()
	bot.msg(user, "Cleared reports.")

@lib.hook(glevel=lib.STAFF, needchan=False)
@lib.hook("<badqid>", "removes a BADQ report")
@lib.argsEQ(1)
def delbadq(bot, user, chan, realtarget, *args):
	try:
		qid = int(args[0])
		del state.db['badqs'][qid]
		state.savedb()
		bot.msg(user, "Removed report #%d" % (qid))
	except:
		bot.msg(user, "Failed!")

@lib.hook(needchan=False)
@lib.help("[<user>]", "shows you or someone else's rank")
def rank(bot, user, chan, realtarget, *args):
	if chan is not None and realtarget == chan.name: replyto = chan
	else: replyto = user

	if len(args) != 0: who = args[0]
	else: who = user

	bot.msg(replyto, "%s is in %d place (%s points). Target is: %s (%s points)." % (who, state.rank(who), state.points(who), state.targetuser(who), state.targetpoints(who)))

@lib.hook(needchan=False)
@lib.help(None, "shows top10 list")
def top10(bot, user, chan, realtarget, *args):
	if len(state.db['ranks']) == 0:
		return bot.msg(state.db['chan'], "No one is ranked!")

	max = len(state.db['ranks'])
	if max > 10:
		max = 10
	replylist = ', '.join(["%s (%s) %s" % (person(x), country(x), pts(x)) for x in range(max)])
	bot.msg(state.db['chan'], "Top 10: %s" % (replylist))

@lib.hook(glevel=lib.ADMIN, needchan=False)
@lib.help("<target score>", "changes the target score for this round")
def settarget(bot, user, chan, realtarget, *args):
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

@lib.hook(needchan=False)
@lib.help("<option>", "votes for a trarget score for next round")
def vote(bot, user, chan, realtarget, *args):
	if state.pointvote is not None:
		if int(args[0]) in state.voteamounts:
			state.voteamounts[int(args[0])] += 1
			bot.msg(user, "Your vote has been recorded.")
		else:
			bot.msg(user, "Sorry - that's not an option!")
	else:
		bot.msg(user, "There's no vote in progress.")

@lib.hook(glevel=lib.ADMIN, needchan=False)
@lib.help("<number>", "sets the max missed question before game stops")
def maxmissed(bot, user, chan, realtarget, *args):
	try:
		state.db['maxmissedquestions'] = int(args[0])
		bot.msg(state.db['chan'], "Max missed questions before round ends has been changed to %s." % (state.db['maxmissedquestions']))
	except:
		bot.msg(user, "Failed to set maxmissed.")

@lib.hook(glevel=lib.ADMIN, needchan=False)
@lib.help("<seconds>", "sets the time between hints")
def hinttimer(bot, user, chan, realtarget, *args):
	try:
		state.db['hinttimer'] = float(args[0])
		bot.msg(state.db['chan'], "Time between hints has been changed to %s." % (state.db['hinttimer']))
	except:
		bot.msg(user, "Failed to set hint timer.")

@lib.hook(glevel=lib.ADMIN, needchan=False)
@lib.help("<number>", "sets the number of hints given")
def hintnum(bot, user, chan, realtarget, *args):
	try:
		state.db['hintnum'] = int(args[0])
		bot.msg(state.db['chan'], "Max number of hints has been changed to %s." % (state.db['hintnum']))
	except:
		bot.msg(user, "Failed to set hintnum.")

@lib.hook(glevel=lib.ADMIN, needchan=False)
@lib.help("<seconds>", "sets the pause between questions")
def questionpause(bot, user, chan, realtarget, *args):
	try:
		state.db['questionpause'] = float(args[0])
		bot.msg(state.db['chan'], "Pause between questions has been changed to %s." % (state.db['questionpause']))
	except:
		bot.msg(user, "Failed to set questionpause.")

@lib.hook(glevel=1, needchan=False)
@lib.help("<full question>", "finds a qid given a complete question")
def findq(bot, user, chan, realtarget, *args):
	if len(args) == 0:
		bot.msg(user, "You need to specify the question.")
		return

	searchkey = ' '.join(args).lower()
	matches = [str(i) for i in range(len(state.db['questions'])) if state.db['questions'][i][0].lower() == searchkey]
	if len(matches) > 1:
		bot.msg(user, "Multiple matches: %s" % (', '.join(matches)))
	elif len(matches) == 1:
		bot.msg(user, "One match: %s" % (matches[0]))
	else:
		bot.msg(user, "No match.")

@lib.hook(glevel=1, needchan=False)
@lib.help("<regex>", "finds a qid given a regex or partial question")
def findqre(bot, user, chan, realtarget, *args):
	if len(args) == 0:
		bot.msg(user, "You need to specify a search string.")
		return

	searcher = re.compile(' '.join(args), re.IGNORECASE)
	matches = [str(i) for i in range(len(state.db['questions'])) if searcher.search(state.db['questions'][i][0]) is not None]
	if len(matches) > 25:
		bot.msg(user, "Too many matches! (>25)")
	elif len(matches) > 1:
		bot.msg(user, "Multiple matches: %s" % (', '.join(matches)))
	elif len(matches) == 1:
		bot.msg(user, "One match: %s" % (matches[0]))
	else:
		bot.msg(user, "No match.")

@lib.hook(glevel=lib.STAFF, needchan=False)
@lib.help("<qid>", "displays the q*a for a qid")
def showq(bot, user, chan, realtarget, *args):
	try:
		qid = int(args[0])
	except:
		bot.msg(user, "Specify a numeric question ID.")
		return
	try:
		q = state.db['questions'][qid]
	except:
		bot.msg(user, "ID not valid.")
		return
	bot.msg(user, "%s: %s*%s" % (qid, q[0], q[1]))

@lib.hook(('delq', 'deleteq'), glevel=lib.STAFF, needchan=False)
@lib.help("<qid>", "removes a question from the database")
def delq(bot, user, chan, realtarget, *args):
	try:
		backup = state.db['questions'][int(args[0])]
		del state.db['questions'][int(args[0])]
		state.savedb()
		bot.msg(user, "Deleted %s*%s" % (backup[0], backup[1]))
	except:
		bot.msg(user, "Couldn't delete that question. %r" % (e))

@lib.hook(glevel=lib.STAFF, needchan=False)
@lib.help("<q>*<a>", "adds a question")
def addq(bot, user, chan, realtarget, *args):
	line = ' '.join([str(arg) for arg in args])
	linepieces = line.split('*')
	if len(linepieces) < 2:
		bot.msg(user, "Error: need <question>*<answer>")
		return
	question = linepieces[0].strip()
	answer = linepieces[1].strip()
	state.db['questions'].append([question, answer])
	state.savedb()
	bot.msg(user, "Done. Question is #%s" % (len(state.db['questions'])-1))


@lib.hook(needchan=False)
def triviahelp(bot, user, chan, realtarget, *args):
	bot.slowmsg(user,             "START")
	bot.slowmsg(user,             "TOP10")
	bot.slowmsg(user,             "POINTS        [<user>]")
	bot.slowmsg(user,             "RANK          [<user>]")
	bot.slowmsg(user,             "BADQ          <reason> (include info to identify question)")
	if user.glevel >= 1:
		bot.slowmsg(user,         "SKIP                            (KNOWN)")
		bot.slowmsg(user,         "STOP                            (KNOWN)")
		bot.slowmsg(user,         "FINDQ         <full question>   (KNOWN)")
		bot.slowmsg(user,         "FINDQRE       <regex>           (KNOWN)")
		bot.slowmsg(user,         "SETNEXTID     <qid>             (KNOWN)")
		if user.glevel >= lib.STAFF:
			bot.slowmsg(user,     "GIVE          <user> [<points>] (STAFF)")
			bot.slowmsg(user,     "SETNEXT       <q>*<a>           (STAFF)")
			bot.slowmsg(user,     "ADDQ          <q>*<a>           (STAFF)")
			bot.slowmsg(user,     "DELQ          <q>*<a>           (STAFF)  [aka DELETEQ]")
			bot.slowmsg(user,     "SHOWQ         <qid>             (STAFF)")
			bot.slowmsg(user,     "BADQS                           (STAFF)")
			bot.slowmsg(user,     "CLEARBADQS                      (STAFF)")
			bot.slowmsg(user,     "DELBADQ       <reportid>        (STAFF)")
			if user.glevel >= lib.ADMIN:
				bot.slowmsg(user, "SETTARGET     <points>          (ADMIN)")
				bot.slowmsg(user, "MAXMISSED     <questions>       (ADMIN)")
				bot.slowmsg(user, "HINTTIMER     <float seconds>   (ADMIN)")
				bot.slowmsg(user, "HINTNUM       <hints>           (ADMIN)")
				bot.slowmsg(user, "QUESTIONPAUSE <float seconds>   (ADMIN)")

@lib.hooknum(417)
def num_417(bot, textline):
#	bot.fastmsg(state.db['chan'], "Whoops, it looks like that question didn't quite go through! (E:417). Let's try another...")
	state.nextquestion(qskipped=False, skipwait=True)

@lib.hooknum(332)
def num_TOPIC(bot, textline):
	pieces = textline.split(None, 4)
	chan = pieces[3]
	if chan != state.db['chan']:
		return
	gottopic = pieces[4][1:]

	formatted = state.db['topicformat'] % {
		'chan': state.db['chan'],
		'top1': "%s (%s)" % (person(0), pts(0)),
		'top3': '/'.join([
			"%s (%s)" % (person(x), pts(x))
			for x in range(3) if x < len(state.db['ranks'])
		]),
		'top3c': ' '.join([
			"%s (%s, %s)" % (person(x), pts(x), country(x))
			for x in range(3) if x < len(state.db['ranks'])
		]),
		'top10': ' '.join([
			"%s (%s)" % (person(x), pts(x))
			for x in range(10) if x < len(state.db['ranks'])
		]),
		'top10c': ' '.join([
			"%s (%s, %s)" % (person(x), pts(x), country(x))
			for x in range(10) if x < len(state.db['ranks'])
		]),
		'lastwinner': state.db['lastwinner'],
		'lastwon': time.strftime("%b %d", time.gmtime(state.db['lastwon'])),
		'target': state.db['target'],
	}
	if gottopic != formatted:
		state.getbot().conn.send("TOPIC %s :%s" % (state.db['chan'], formatted))


def specialQuestion(oldq):
	newq = [oldq[0], oldq[1]]
	qtype = oldq[0].upper()

	if qtype == "!MONTH":
		newq[0] = "What month is it currently (in UTC)?"
		newq[1] = time.strftime("%B", time.gmtime()).lower()
	elif qtype == "!MATH+":
		randnum1 = random.randrange(0, 11)
		randnum2 = random.randrange(0, 11)
		newq[0] = "What is %d + %d?" % (randnum1, randnum2)
		newq[1] = spellout(randnum1+randnum2)
	return newq

def spellout(num):
	return [
		"zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
		"nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
		"sixteen", "seventeen", "eighteen", "nineteen", "twenty"
	][num]
