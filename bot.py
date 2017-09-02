#!/usr/bin/python

# Erebus IRC bot - Author: John Runyon
# "Bot" and "BotConnection" classes (handling a specific "arm")

import socket, sys, time, threading, os, random
from collections import deque

#bots = {'erebus': bot.Bot(nick='Erebus', user='erebus', bind='', server='irc.quakenet.org', port=6667, realname='Erebus')}
class Bot(object):
	def __init__(self, parent, nick, user, bind, authname, authpass, server, port, realname):
		self.parent = parent
		self.nick = nick
		self.permnick = nick
		self.user = user
		self.realname = realname

		self.authname = authname
		self.authpass = authpass

		curs = self.parent.db.cursor()
		if curs.execute("SELECT chname FROM chans WHERE bot = %s AND active = 1", (self.nick,)):
			chansres = curs.fetchall()
			curs.close()
			self.chans = [self.parent.newchannel(self, row['chname']) for row in chansres]

		self.conn = BotConnection(self, bind, server, port)

		self.msgqueue = deque()
		self.slowmsgqueue = deque()
		self.makemsgtimer()
		self.msgtimer.start()

	def __del__(self):
		curs = self.parent.db.cursor()
		curs.execute("UPDATE bots SET connected = 0 WHERE nick = %s", (self.nick,))
		curs.close()


	def log(self, *args, **kwargs):
		self.parent.log(self.nick, *args, **kwargs)

	def connect(self):
		if self.conn.connect():
			self.parent.newfd(self, self.conn.socket.fileno())

	def getdata(self):
		return self.conn.read()

	def _checknick(self): # check if we're using the right nick, try changing
		if self.nick != self.permnick and self.conn.registered():
			self.conn.send("NICK %s" % (self.permnick))

	def parse(self, line):
		self.log('I', line)
		pieces = line.split()

		# dispatch dict
		zero = { #things to look for without source
			'NOTICE': self._gotconnected,
			'PING': self._gotping,
			'ERROR': self._goterror,
		}
		one = { #things to look for after source
			'001': self._got001,
			'376': self._gotRegistered,
			'422': self._gotRegistered,
			'PRIVMSG': self._gotprivmsg,
			'353': self._got353, #NAMES
			'354': self._got354, #WHO
			'433': self._got433, #nick in use
			'JOIN': self._gotjoin,
			'PART': self._gotpart,
			'QUIT': self._gotquit,
			'NICK': self._gotnick,
			'MODE': self._gotmode,
		}

		if self.parent.hasnumhook(pieces[1]):
			hooks = self.parent.getnumhook(pieces[1])
			for callback in hooks:
				try:
					callback(self, line)
				except Exception:
					self.__debug_cbexception("numhook", line)

		if pieces[0] in zero:
			zero[pieces[0]](pieces)
		elif pieces[1] in one:
			one[pieces[1]](pieces)

	def _gotconnected(self, pieces):
		if not self.conn.registered():
			self.conn.register()
	def _gotping(self, pieces):
		self.conn.send("PONG %s" % (pieces[1]))
		self._checknick()
	def _goterror(self, pieces): #TODO handle more gracefully
		curs = self.parent.db.cursor()
		curs.execute("UPDATE bots SET connected = 0")
		curs.close()
		sys.exit(2)
		os._exit(2)
	def _got001(self, pieces):
		pass # wait until the end of MOTD instead
	def _gotRegistered(self, pieces):
		self.conn.registered(True)

		curs = self.parent.db.cursor()
		curs.execute("UPDATE bots SET connected = 1 WHERE nick = %s", (self.nick,))
		curs.close()

		self.conn.send("MODE %s +x" % (pieces[2]))
		if self.authname is not None and self.authpass is not None:
			self.conn.send("AUTH %s %s" % (self.authname, self.authpass))
		for c in self.chans:
			self.join(c.name)
	def _gotprivmsg(self, pieces):
		nick = pieces[0].split('!')[0][1:]
		user = self.parent.user(nick)
		target = pieces[2]
		msg = ' '.join(pieces[3:])[1:]
		self.parsemsg(user, target, msg)
	def _got353(self, pieces):
		chan = self.parent.channel(pieces[4])
		names = pieces[5:]
		names[0] = names[0][1:] #remove colon
		for n in names:
			user = self.parent.user(n.lstrip('@+'))
			if n[0] == '@':
				chan.userjoin(user, 'op')
			elif n[0] == '+':
				chan.userjoin(user, 'voice')
			else:
				chan.userjoin(user)
			user.join(chan)
	def _got354(self, pieces):
		qt = int(pieces[3])
		if qt < 3:
			nick, auth = pieces[4:6]
			chan = None
		else:
			chan, nick, auth = pieces[4:7]
			chan = self.parent.channel(chan)
		user = self.parent.user(nick)
		user.authed(auth)

		if chan is not None:
			user.join(chan)
			chan.userjoin(user)

		if qt == 2: # triggered by !auth
			if user.isauthed():
				if user.glevel > 0:
					self.msg(nick, "You are now known as #%s (access level: %s)" % (auth, user.glevel))
				else:
					self.msg(nick, "You are now known as #%s (not staff)" % (auth))
			else:
				self.msg(nick, "I tried, but you're not authed!")
	def _got433(self, pieces):
		if not self.conn.registered(): #we're trying to connect
			newnick = "%s%d" % (self.nick, random.randint(111,999))
			self.conn.send("NICK %s" % (newnick))
			self.nick = newnick
	def _gotjoin(self, pieces):
		nick = pieces[0].split('!')[0][1:]
		chan = self.parent.channel(pieces[2])

		if nick == self.nick:
			self.conn.send("WHO %s c%%cant,3" % (chan))
		else:
			user = self.parent.user(nick, justjoined=True)
			chan.userjoin(user)
			user.join(chan)
	def _gotpart(self, pieces):
		nick = pieces[0].split('!')[0][1:]
		chan = self.parent.channel(pieces[2])

		if nick != self.nick:
			gone = self.parent.user(nick).part(chan)
			chan.userpart(self.parent.user(nick))
			if gone:
				self.parent.user(nick).quit()
				del self.parent.users[nick.lower()]
	def _gotquit(self, pieces):
		nick = pieces[0].split('!')[0][1:]
		if nick != self.nick:
			for chan in self.parent.user(nick).chans:
				chan.userpart(self.parent.user(nick))
			self.parent.user(nick).quit()
			del self.parent.users[nick.lower()]
	def _gotnick(self, pieces):
		oldnick = pieces[0].split('!')[0][1:]
		newnick = pieces[2][1:]
		if newnick.lower() != oldnick.lower():
			self.parent.users[newnick.lower()] = self.parent.users[oldnick.lower()]
			del self.parent.users[oldnick.lower()]
		self.parent.users[newnick.lower()].nickchange(newnick)
	def _gotmode(self, pieces):
		source = pieces[0].split('!')[0][1:]
		chan = self.parent.channel(pieces[2])
		mode = pieces[3]
		args = pieces[4:]

		adding = True
		for c in mode:
			if c == '+':
				adding = True
			elif c == '-':
				adding = False
			elif c == 'o':
				if adding:
					chan.userop(self.parent.user(args.pop(0)))
				else:
					chan.userdeop(self.parent.user(args.pop(0)))
			elif c == 'v':
				if adding:
					chan.uservoice(self.parent.user(args.pop(0)))
				else:
					chan.userdevoice(self.parent.user(args.pop(0)))
			else:
				pass # don't care about other modes

	def __debug_cbexception(self, source, *args, **kwargs):
		if int(self.parent.cfg.get('debug', 'cbexc', default=0)) == 1:
			self.conn.send("PRIVMSG %s :%09.3f 4!!! CBEXC %s" % (self.parent.cfg.get('debug', 'owner'), time.time() % 100000, source))
			__import__('traceback').print_exc()
			self.log('!', "CBEXC %s %r %r" % (source, args, kwargs))
#			print "%09.3f %s [!] CBEXC %s %r %r" % (time.time() % 100000, self.nick, source, args, kwargs)


	def parsemsg(self, user, target, msg):
		chan = None
		if len(msg) == 0:
			return

		triggerused = msg[0] == self.parent.trigger
		if triggerused: msg = msg[1:]
		pieces = msg.split()

		if target == self.nick:
			if msg[0] == "\001": #ctcp
				msg = msg.strip("\001")
				if msg == "VERSION":
					self.msg(user, "\001VERSION Erebus v%d.%d - http://github.com/zonidjan/erebus" % (self.parent.APIVERSION, self.parent.RELEASE))
				return
			if len(pieces) > 1:
				chanword = pieces[1]
				if chanword[0] == '#':
					chan = self.parent.channel(chanword)
					if chan is not None: #if chan is still none, there's no bot on "chanword", and chanword is used as a parameter.
						pieces.pop(1)

		else: # message was sent to a channel
			chan = self.parent.channel(target)
			try:
				if msg[0] == '*': # message may be addressed to bot by "*BOTNICK" trigger?
					if pieces[0][1:].lower() == self.nick.lower():
						pieces.pop(0) # command actually starts with next word
						msg = ' '.join(pieces) # command actually starts with next word
				elif not triggerused:
					if self.parent.haschanhook(target.lower()):
						for callback in self.parent.getchanhook(target.lower()):
							try:
								cbret = callback(self, user, chan, *pieces)
							except NotImplementedError:
								self.msg(user, "Command not implemented.")
							except:
								self.msg(user, "Command failed. Code: CBEXC%09.3f" % (time.time() % 100000))
								self.__debug_cbexception("chanhook", user=user, target=target, msg=msg)
					return # not to bot, don't process!
			except IndexError:
				return # "message" is empty

		cmd = pieces[0].lower()

		if self.parent.hashook(cmd):
			for callback in self.parent.gethook(cmd):
				if chan is None and callback.needchan:
					self.msg(user, "You need to specify a channel for that command.")
				elif user.glevel >= callback.reqglevel and (not callback.needchan or chan.levelof(user.auth) >= callback.reqclevel):
					try:
						cbret = callback(self, user, chan, target, *pieces[1:])
					except NotImplementedError:
						self.msg(user, "Command not implemented.")
					except Exception:
						self.msg(user, "Command failed. Code: CBEXC%09.3f" % (time.time() % 100000))
						self.__debug_cbexception("hook", user=user, target=target, msg=msg)
					except SystemExit as e:
						curs = self.parent.db.cursor()
						curs.execute("UPDATE bots SET connected = 0")
						curs.close()
						raise e
		else:
			self.msg(user, "I don't know that command.")

	def __debug_nomsg(self, target, msg):
		if int(self.parent.cfg.get('debug', 'nomsg', default=0)) == 1:
			self.conn.send("PRIVMSG %s :%09.3f 4!!! NOMSG %r, %r" % (self.parent.cfg.get('debug', 'owner'), time.time() % 100000, target, msg))
			self.log('!', "!!! NOMSG")
#			print "%09.3f %s [!] %s" % (time.time() % 100000, self.nick, "!!! NOMSG")
			__import__('traceback').print_stack()

	def msg(self, target, msg):
		cmd = self._formatmsg(target, msg)
		if self.conn.exceeded or self.conn.bytessent+len(cmd) >= self.conn.recvq:
			self.msgqueue.append(cmd)
		else:
			self.conn.send(cmd)
		self.conn.exceeded = True

	def slowmsg(self, target, msg):
		cmd = self._formatmsg(target, msg)
		if self.conn.exceeded or self.conn.bytessent+len(cmd) >= self.conn.recvq:
			self.slowmsgqueue.append(cmd)
		else:
			self.conn.send(cmd)
		self.conn.exceeded = True

	def fastmsg(self, target, msg):
		self.conn.send(self._formatmsg(target, msg))
		self.conn.exceeded = True

	def _formatmsg(self, target, msg):
		if target is None or msg is None:
			return self.__debug_nomsg(target, msg)

		target = str(target)

		if target[0] == '#': command = "PRIVMSG %s :%s" % (target, msg)
		else: command = "NOTICE %s :%s" % (target, msg)

		return command

	def _popmsg(self):
		self.makemsgtimer()
		self.conn.bytessent -= self.conn.recvq/3
		if self.conn.bytessent < 0: self.conn.bytessent = 0
		self.conn.exceeded = False

		try:
			cmd = self.msgqueue.popleft()
			if not self.conn.exceeded and self.conn.bytessent+len(cmd) < self.conn.recvq:
				self.conn.send(cmd)
				self.conn.exceeded = True
			else: raise IndexError
		except IndexError:
			try:
				cmd = self.slowmsgqueue.popleft()
				if not self.conn.exceeded and self.conn.bytessent+len(cmd) < self.conn.recvq:
					self.conn.send(cmd)
					self.conn.exceeded = True
			except IndexError:
				pass
		self.msgtimer.start()

	def makemsgtimer(self):
		self.msgtimer = threading.Timer(3, self._popmsg)
		self.msgtimer.daemon = True

	def join(self, chan):
		self.conn.send("JOIN %s" % (chan))

	def part(self, chan):
		self.conn.send("PART %s" % (chan))

	def quit(self, reason="Shutdown"):
		self.conn.send("QUIT :%s" % (reason))

	def __str__(self): return self.nick
	def __repr__(self): return "<Bot %r>" % (self.nick)

class BotConnection(object):
	def __init__(self, parent, bind, server, port):
		self.parent = parent
		self.buffer = ''
		self.socket = None

		self.bind = bind
		self.server = server
		self.port = int(port)

		self.state = 0 # 0=disconnected, 1=registering, 2=connected

		self.bytessent = 0
		self.recvq = 500
		self.exceeded = False

	def connect(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind((self.bind, 0))
		self.socket.connect((self.server, self.port))
		return True
	def register(self):
		if self.state == 0:
			self.send("NICK %s" % (self.parent.nick))
			self.send("USER %s 0 * :%s" % (self.parent.user, self.parent.realname))
			self.state = 1
		return True

	def registered(self, done=False):
		if done: self.state = 2
		return self.state == 2

	def send(self, line):
		self.parent.log('O', line)
#		print "%09.3f %s [O] %s" % (time.time() % 100000, self.parent.nick, line)
		self.bytessent += len(line)
		self._write(line)

	def _write(self, line):
		self.socket.sendall(line+"\r\n")

	def read(self):
		self.buffer += self.socket.recv(8192)
		lines = []

		while "\r\n" in self.buffer:
			pieces = self.buffer.split("\r\n", 1)
#			self.parent.log('I', pieces[0]) # replaced by statement in Bot.parse()
#			print "%09.3f %s [I] %s" % (time.time() % 100000, self.parent.nick, pieces[0])
			lines.append(pieces[0])
			self.buffer = pieces[1]

		return lines

	def __str__(self): return self.parent.nick
	def __repr__(self): return "<BotConnection %r (%r)>" % (self.socket.fileno(), self.parent.nick)
