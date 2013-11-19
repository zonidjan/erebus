#!/usr/bin/python

#TODO: error checking

import socket

#bots = {'erebus': bot.Bot(nick='Erebus', user='erebus', bind='', server='irc.quakenet.org', port=6667, realname='Erebus')}
class Bot(object):
	def __init__(self, parent, nick, user, bind, server, port, realname, chans):
		self.parent = parent
		self.nick = nick
		self.chans = chans

		self.conn = BotConnection(self, nick, user, bind, server, port, realname)
	def connect(self):
		self.conn.connect()
	def getdata(self):
		for line in self.conn.read():
			self.parse(line)
	def parse(self, line):
		pieces = line.split()
		if not self.conn.registered():
			if pieces[0] == "PING":
				self.conn.send("PONG %s" % (pieces[1]))
			elif pieces[1] == "001":
				self.conn.registered(True)
				print "!!!REGISTERED!!!"

class BotConnection(object):
	state = 0 # 0=disconnected, 1=registering, 2=connected

	def __init__(self, parent, nick, user, bind, server, port, realname):
		self.parent = parent
		self.buffer = ''
		self.socket = None

		self.nick = nick
		self.user = user
		self.bind = bind
		self.server = server
		self.port = int(port)
		self.realname = realname

	def connect(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind((self.bind, 0))
		self.socket.connect((self.server, self.port))
		self.send("NICK %s" % (self.nick))
		self.send("USER %s 0 * :%s" % (self.user, self.realname))
		self.state = 1

	def registered(self, done=False):
		if done: self.state = 2
		return self.state == 2

	def fileno(self):
		if self.socket is not None:
			return self.socket.fileno()
		else:
			return None

	#TODO: rewrite send() to queue
	def send(self, line):
		self.write(line)
	def write(self, line):
		print self.nick, '[O]', line
		self.socket.sendall(line+"\r\n")
	def read(self):
		self.buffer += self.socket.recv(8192)
		lines = []
		while '\r\n' in self.buffer:
			pieces = self.buffer.split('\r\n', 1)
			print self.nick, '[I]', pieces[0]
			lines.append(pieces[0])
			self.buffer = pieces[1]
		return lines
