#!/usr/bin/python

# Erebus IRC bot - Author: John Runyon
# "Bot" and "BotConnection" classes (handling a specific "arm")

import socket, sys

#bots = {'erebus': bot.Bot(nick='Erebus', user='erebus', bind='', server='irc.quakenet.org', port=6667, realname='Erebus')}
class Bot(object):
	def __init__(self, parent, nick, user, bind, authname, authpass, server, port, realname):
		self.parent = parent
		self.nick = nick
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
	def connect(self):
		if self.conn.connect():
			self.parent.newfd(self, self.conn.socket.fileno())

	def getdata(self):
		return self.conn.read()

	def parse(self, line):
		pieces = line.split()

		if not self.conn.registered() and pieces[0] == "NOTICE":
			self.conn.register()
			return

		if self.parent.hasnumhook(pieces[1]):
			hooks = self.parent.getnumhook(pieces[1])
			for callback in hooks:
				callback(self, line)

		if pieces[1] == "001":
			self.conn.registered(True)
			self.conn.send("MODE %s +x" % (pieces[2]))
			if self.authname is not None and self.authpass is not None:
				self.conn.send("AUTH %s %s" % (self.authname, self.authpass))
			for c in self.chans:
				self.join(c.name)

		elif pieces[1] == "PRIVMSG":
			nick = pieces[0].split('!')[0][1:]
			user = self.parent.user(nick)
			target = pieces[2]
			msg = ' '.join(pieces[3:])[1:]
			self.parsemsg(user, target, msg)

		elif pieces[0] == "PING":
			self.conn.send("PONG %s" % (pieces[1]))

		elif pieces[1] == "354": # WHOX
			qt = pieces[3]
			nick = pieces[4]
			auth = pieces[5]
			self.parent.user(nick).authed(auth)

		elif pieces[1] == "JOIN":
			nick = pieces[0].split('!')[0][1:]
			chan = self.parent.channel(pieces[2])

			if nick == self.nick:
				self.conn.send("WHO %s c%%ant,1" % (chan))
			else:
				user = self.parent.user(nick, justjoined=True)
				chan.userjoin(user)
				user.join(chan)

		elif pieces[1] == "PART":
			nick = pieces[0].split('!')[0][1:]
			chan = self.parent.channel(pieces[2])
			
			if nick != self.nick:
				self.parent.user(nick).part(chan)
				chan.userpart(self.parent.user(nick))

		elif pieces[1] == "QUIT":
			nick = pieces[0].split('!')[0][1:]
			if nick != self.nick:
				self.parent.user(nick).quit()
				del self.parent.users[nick.lower()]

		elif pieces[1] == "NICK":
			oldnick = pieces[0].split('!')[0][1:]
			newnick = pieces[2][1:]
			if newnick.lower() != oldnick.lower():
				self.parent.users[newnick.lower()] = self.parent.users[oldnick.lower()]
				del self.parent.users[oldnick.lower()]
			self.parent.users[newnick.lower()].nick(newnick)

		elif pieces[1] == "MODE": #TODO parse for ops/voices (at least)
			pass

	
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
							cbret = callback(self, user, chan, *pieces)
							if cbret is NotImplemented:
								self.msg(user, "Command not implemented.")
					return # not to bot, don't process!
			except IndexError:
				return # "message" is empty

		cmd = pieces[0].lower()

		if self.parent.hashook(cmd):
			for callback in self.parent.gethook(cmd):
				if chan is None and callback.needchan:
					self.msg(user, "You need to specify a channel for that command.")
				elif user.glevel >= callback.reqglevel and (not callback.needchan or chan.levelof(user.auth) >= callback.reqclevel):
					cbret = callback(self, user, chan, target, *pieces[1:])
					if cbret is NotImplemented:
						self.msg(user, "Command not implemented.")

	def msg(self, target, msg):
		if target is None or msg is None: return

		if isinstance(target, self.parent.User): self.conn.send("NOTICE %s :%s" % (target.nick, msg))
		elif isinstance(target, self.parent.Channel): self.conn.send("PRIVMSG %s :%s" % (target.name, msg))
		elif isinstance(target, basestring):
			if target[0] == '#': self.conn.send("PRIVMSG %s :%s" % (target, msg))
			else: self.conn.send("NOTICE %s :%s" % (target, msg))
		else: raise TypeError('Bot.msg() "target" must be Erebus.User, Erebus.Channel, or string')

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

	#TODO: rewrite send() to queue
	def send(self, line):
		print self.parent.nick, '[O]', str(line)
		self._write(line)

	def _write(self, line):
		self.socket.sendall(line+"\r\n")

	def read(self):
		self.buffer += self.socket.recv(8192)
		lines = []

		while "\r\n" in self.buffer:
			pieces = self.buffer.split("\r\n", 1)
			print self.parent.nick, '[I]', pieces[0]
			lines.append(pieces[0])
			self.buffer = pieces[1]

		return lines

	def __str__(self): return self.nick
	def __repr__(self): return "<BotConnection %r (%r)>" % (self.socket.fileno(), self.parent.nick)
