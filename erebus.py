#!/usr/bin/python

# Erebus IRC bot - Author: John Runyon
# main startup code

#TODO: tons

import os, sys, select, MySQLdb, MySQLdb.cursors
import bot, config, ctlmod

class Erebus(object):
	bots = {}
	fds = {}
	mods = {}
	msghandlers = {}
	users = {}
	chans = {}

	class User(object):
		chans = []

		def __init__(self, nick, auth=None):
			print "parent.User(self, %r, %r)" % (nick, auth)
			self.nick = nick
			self.auth = auth
			self.checklevel()

		def isauthed(self):
			return self.auth is not None

		def authed(self, auth):
			if auth == '0': auth = None
			self.auth = auth
			self.checklevel()

		def checklevel(self):
			if self.auth is None:
				self.level = -1
			else:
				c = main.db.cursor()
				c.execute("SELECT level FROM users WHERE auth = %s", (self.auth,))
				row = c.fetchone()
				if row is not None:
					self.level = row['level']
				else:
					self.level = 0
			return self.level

		def __str__(self): return self.nick
		def __repr__(self): return "<User %r (%d)>" % (self.nick,self.level)

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

	def __init__(self, trigger):
		self.trigger = trigger
		if os.name == "posix":
			self.potype = "poll"
			self.po = select.poll()
		else: # f.e. os.name == "nt" (Windows)
			self.potype = "select"
			self.fdlist = []

	def newbot(self, nick, user, bind, server, port, realname, chans):
		if bind is None: bind = ''
		obj = bot.Bot(self, nick, user, bind, server, port, realname, chans)
		self.bots[nick.lower()] = obj

	def newfd(self, obj, fileno):
		self.fds[fileno] = obj
		if self.potype == "poll":
			self.po.register(fileno, select.POLLIN)
		elif self.potype == "select":
			self.fdlist.append(fileno)

	def bot(self, name): #get Bot() by name (nick)
		return self.bots[name.lower()]
	def fd(self, fileno): #get Bot() by fd/fileno
		return self.fds[fileno]

	def user(self, nick):
		nick = nick.lower()
		if nick in self.users:
			return self.users[nick]
		else:
			user = self.User(nick)
			self.users[nick] = user
			return user
	def channel(self, name): #TODO #get Channel() by name
		return self.Channel(name.lower())

	def poll(self):
		if self.potype == "poll":
			return [fd for (fd, ev) in self.po.poll()]
		elif self.potype == "select":
			return select.select(self.fdlist, [], [])[0]

	def connectall(self):
		for bot in self.bots.itervalues():
			if bot.conn.state == 0:
				bot.connect()

	#bind functions
	def hook(self, word, handler):
		self.msghandlers[word] = handler
	def unhook(self, word):
		del self.msghandlers[word]
	def hashook(self, word):
		return word in self.msghandlers
	def gethook(self, word):
		return self.msghandlers[word]

def setup():
	global cfg, main

	cfg = config.Config('bot.config')
	main = Erebus(cfg.trigger)

	autoloads = [mod for mod, yes in cfg.items('autoloads') if int(yes) == 1]
	print autoloads
	for mod in autoloads:
		ctlmod.load(main, mod)

	main.db = MySQLdb.connect(host=cfg.dbhost, user=cfg.dbuser, passwd=cfg.dbpass, db=cfg.dbname, cursorclass=MySQLdb.cursors.DictCursor)
	c = main.db.cursor()
	c.execute("SELECT nick, user, bind FROM bots WHERE active = 1")
	rows = c.fetchall()
	c.close()
	for row in rows:
		c2 = main.db.cursor()
		c2.execute("SELECT chname FROM chans WHERE bot = %s AND active = 1", (row['nick'],))
		chans = [chdic['chname'] for chdic in c2.fetchall()]
		c2.close()
		main.newbot(row['nick'], row['user'], row['bind'], cfg.host, cfg.port, cfg.realname, chans)
	main.connectall()

def loop():
	poready = main.poll()
	for fileno in poready:
		main.fd(fileno).getdata()

if __name__ == '__main__':
	setup()
	while True: loop()
