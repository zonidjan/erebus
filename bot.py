#!/usr/bin/python

#TODO: error checking

import socket, sys

#bots = {'erebus': bot.Bot(nick='Erebus', user='erebus', bind='', server='irc.quakenet.org', port=6667, realname='Erebus')}
class Bot(object):
	def __init__(self, parent, nick, user, bind, server, port, realname, chans):
		self.parent = parent
		self.nick = nick
		self.user = user
		self.realname = realname
		self.chans = chans

		self.conn = BotConnection(self, bind, server, port)
	def connect(self):
		if self.conn.connect():
			self.parent.newfd(self, self.conn.socket.fileno())

	def getdata(self):
		for line in self.conn.read():
			print self.nick, '[I]', line

			if not self.conn.registered():
				pieces = line.split()

				if pieces[0] == "PING":
					self.conn.send("PONG %s" % (pieces[1]))

				elif pieces[1] == "001":
					self.conn.registered(True)
					for c in self.chans:
						self.join(c)

			else:
				self.parse(line)
	def parse(self, line):
		pieces = line.split()

		if pieces[1] == "PRIVMSG":
			nick = pieces[0].split('!')[0][1:]
			user = self.parent.user(nick)
			chan = self.parent.channel(pieces[2])
			msg = ' '.join(pieces[3:])[1:]
			self.parsemsg(user, chan, msg)

		elif pieces[0] == "PING":
			self.conn.send("PONG %s" % (pieces[1]))

		elif pieces[1] == "JOIN":
			nick = pieces[0].split('!')[0][1:]
			user = self.parent.user(nick)
			chan = self.parent.channel(pieces[2]) #TODO TODO TODO
			
	def parsemsg(self, user, chan, msg):
		if msg[0] == '!': #TODO check config for trigger
			msg = msg[1:]
		else:
			return

		pieces = msg.split()
		cmd = pieces[0].lower()

		if self.parent.hashook(cmd):
			self.parent.gethook(cmd)(self, user, chan, *pieces[1:])

	def msg(self, target, msg):
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
	state = 0 # 0=disconnected, 1=registering, 2=connected

	def __init__(self, parent, bind, server, port):
		self.parent = parent
		self.buffer = ''
		self.socket = None

		self.bind = bind
		self.server = server
		self.port = int(port)

	def connect(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind((self.bind, 0))
		self.socket.connect((self.server, self.port))
		self.send("NICK %s" % (self.parent.nick))
		self.send("USER %s 0 * :%s" % (self.parent.user, self.parent.realname))
		self.state = 1
		return True

	def registered(self, done=False):
		if done: self.state = 2
		return self.state == 2

	#TODO: rewrite send() to queue
	def send(self, line):
		print self.parent.nick, '[O]', line
		self.write(line)

	def write(self, line):
		self.socket.sendall(line+"\r\n")

	def read(self):
		self.buffer += self.socket.recv(8192)
		lines = []

		while '\r\n' in self.buffer:
			pieces = self.buffer.split('\r\n', 1)
			lines.append(pieces[0])
			self.buffer = pieces[1]

		return lines

	def __str__(self): return self.nick
	def __repr__(self): return "<BotConnection %r (%r)>" % (self.socket.fileno(), self.parent.nick)
