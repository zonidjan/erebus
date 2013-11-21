#!/usr/bin/python

#TODO: tons

import sys, select
import bot

class Erebus(object):
	bots = {}
	fds = {}
	mods = {}
	msghandlers = {}

	class User(object):
		chans = []

		def __init__(self, nick, auth=None):
			self.nick = nick
			self.auth = auth

			if auth is not None:
				self.checklevel()

		def authed(self, auth):
			self.auth = auth
			self.checklevel()

		def checklevel(self): self.level = 9999 #TODO get level from db
		def __str__(self): return self.nick
		def __repr__(self): return "<User %r>" % (self.nick)
	class Channel(object):
		users = []
		voices = []
		ops = []

		def __init__(self, name):
			self.name = name

		def userjoin(self, user, level=None):
			if user not in self.users: self.users.append(user)
			if level == 'op' and user not in self.ops: self.ops.append(user)
			if level == 'voice' and user not in self.voices: self.voices.append(user)

		def userpart(self, user):
			if user in self.ops: self.ops.remove(user)
			if user in self.voices: self.voices.remove(user)
			if user in self.users: self.users.remove(user)

		def userop(self, user):
			if user in self.users and user not in self.ops: self.ops.append(user)

		def uservoice(self, user):
			if user in self.users and user not in self.voices: self.voices.append(user)

		def userdeop(self, user):
			if user in self.ops: self.ops.remove(user)

		def userdevoice(self, user):
			if user in self.voices: self.voices.remove(user)

		def __str__(self): return self.name
		def __repr__(self): return "<Channel %r>" % (self.name)

	def __init__(self):
		self.po = select.poll()

	def newbot(self, nick, user, bind, server, port, realname, chans):
		if bind is None: bind = ''
		obj = bot.Bot(self, nick, user, bind, server, port, realname, chans)
		self.bots[nick.lower()] = obj

	def newfd(self, obj, fileno):
		print "newfd(Erebus(), %r, %r)" % (obj, fileno)
		self.fds[fileno] = obj
		self.po.register(fileno, select.POLLIN)

	def bot(self, name):
		return self.bots[name.lower()]

	def fd(self, fileno):
		return self.fds[fileno]

	def user(self, nick): #TODO
		return self.User(nick.lower())

	def channel(self, name): #TODO
		return self.Channel(name.lower())

	def poll(self):
		return self.po.poll(60000)

	def connectall(self):
		for bot in self.bots.itervalues():
			if bot.conn.state == 0:
				bot.connect()

	#module functions
	def modlist(self): pass
	def hasmod(self, name): pass
	def loadmod(self, name): pass
	def unloadmod(self, name): pass
	def reloadmod(self, name): pass

	#bind functions
	def bind(self, word, handler): pass
	def addbind(self, word, handler): pass
	def rmbind(self, word, handler): pass
	def getbind(self, word, handler): pass


main = Erebus()

def setup():
	main.newbot('Erebus', 'erebus', None, 'irc.quakenet.org', 6667, 'Erebus', ['#dimetest'])
	main.bot('erebus').connect()

def loop():
	poready = main.poll()

	for (fileno,mask) in poready:
		main.fd(fileno).getdata()

if __name__ == '__main__':
	setup()
	while True: loop()
