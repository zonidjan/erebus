#!/usr/bin/python
# vim: fileencoding=utf-8

# Erebus IRC bot - Author: John Runyon
# main startup code

from __future__ import print_function

import os, sys, select, MySQLdb, MySQLdb.cursors, time, random, gc
import bot, config, ctlmod

class Erebus(object): #singleton to pass around
	APIVERSION = 0
	RELEASE = 0

	bots = {}
	fds = {}
	numhandlers = {}
	msghandlers = {}
	chanhandlers = {}
	users = {}
	chans = {}

	class User(object):
		def __init__(self, nick, auth=None):
			self.nick = nick
			self.auth = auth
			self.checklevel()

			self.chans = []

		def msg(self, *args, **kwargs):
			main.randbot().msg(self, *args, **kwargs)
		def slowmsg(self, *args, **kwargs):
			main.randbot().slowmsg(self, *args, **kwargs)
		def fastmsg(self, *args, **kwargs):
			main.randbot().fastmsg(self, *args, **kwargs)

		def isauthed(self):
			return self.auth is not None

		def authed(self, auth):
			if auth == '0': self.auth = None
			else: self.auth = auth.lower()
			self.checklevel()

		def checklevel(self):
			if self.auth is None:
				self.glevel = -1
			else:
				c = main.query("SELECT level FROM users WHERE auth = %s", (self.auth,))
				if c:
					row = c.fetchone()
					if row is not None:
						self.glevel = row['level']
					else:
						self.glevel = 0
				else:
					self.glevel = 0
			return self.glevel

		def join(self, chan):
			if chan not in self.chans: self.chans.append(chan)
		def part(self, chan):
			try:
				self.chans.remove(chan)
			except: pass
			return len(self.chans) == 0
		def quit(self):
			pass
		def nickchange(self, newnick):
			self.nick = newnick

		def __str__(self): return self.nick
		def __repr__(self): return "<User %r (%d)>" % (self.nick, self.glevel)

	class Channel(object):
		def __init__(self, name, bot):
			self.name = name
			self.bot = bot
			self.levels = {}

			self.users = []
			self.voices = []
			self.ops = []

			c = main.query("SELECT user, level FROM chusers WHERE chan = %s", (self.name,))
			if c:
				row = c.fetchone()
				while row is not None:
					self.levels[row['user']] = row['level']
					row = c.fetchone()


		def msg(self, *args, **kwargs):
			self.bot.msg(self, *args, **kwargs)
		def slowmsg(self, *args, **kwargs):
			self.bot.slowmsg(self, *args, **kwargs)
		def fastmsg(self, *args, **kwargs):
			self.bot.fastmsg(self, *args, **kwargs)

		def levelof(self, auth):
			if auth is None:
				return 0
			auth = auth.lower()
			if auth in self.levels:
				return self.levels[auth]
			else:
				return 0

		def setlevel(self, auth, level, savetodb=True):
			auth = auth.lower()
			if savetodb:
				c = main.query("REPLACE INTO chusers (chan, user, level) VALUES (%s, %s, %s)", (self.name, auth, level))
				if c:
					self.levels[auth] = level
					return True
				else:
					return False

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

	def __init__(self, cfg):
		self.starttime = time.time()
		self.cfg = cfg
		self.trigger = cfg.trigger
		if os.name == "posix":
			self.potype = "poll"
			self.po = select.poll()
		else: # f.e. os.name == "nt" (Windows)
			self.potype = "select"
			self.fdlist = []

	def query(self, *args, **kwargs):
		if 'noretry' in kwargs:
			noretry = kwargs['noretry']
			del kwargs['noretry']
		else:
			noretry = False

		self.log("[SQL]", "?", "query(%s, %s)" % (', '.join([repr(i) for i in args]), ', '.join([str(key)+"="+repr(kwargs[key]) for key in kwargs])))
		try:
			curs = self.db.cursor()
			res = curs.execute(*args, **kwargs)
			if res:
				return curs
			else:
				return res
		except MySQLdb.MySQLError as e:
			self.log("[SQL]", "!", "MySQL error! %r" % (e))
			if not noretry:
				dbsetup()
				return self.query(*args, noretry=True, **kwargs)
			else:
				raise e

	def querycb(self, cb, *args, **kwargs):
		def run_query():
			cb(self.query(*args, **kwargs))
		threading.Thread(target=run_query).start()

	def newbot(self, nick, user, bind, authname, authpass, server, port, realname):
		if bind is None: bind = ''
		obj = bot.Bot(self, nick, user, bind, authname, authpass, server, port, realname)
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
	def randbot(self): #get Bot() randomly
		return self.bots[random.choice(list(self.bots.keys()))]

	def user(self, _nick, justjoined=False, create=True):
		nick = _nick.lower()
		if nick in self.users:
			return self.users[nick]
		elif create:
			user = self.User(_nick)
			self.users[nick] = user

			if justjoined:
				self.randbot().conn.send("WHO %s n%%ant,1" % (nick))

			return user
		else:
			return None
	def channel(self, name): #get Channel() by name
		if name.lower() in self.chans:
			return self.chans[name.lower()]
		else:
			return None

	def newchannel(self, bot, name):
		chan = self.Channel(name.lower(), bot)
		self.chans[name.lower()] = chan
		return chan

	def poll(self):
		if self.potype == "poll":
			return [fd for (fd, ev) in self.po.poll()]
		elif self.potype == "select":
			return select.select(self.fdlist, [], [])[0]

	def connectall(self):
		for bot in self.bots.values():
			if bot.conn.state == 0:
				bot.connect()

	def module(self, name):
		return ctlmod.modules[name]

	def log(self, source, level, message):
		print("%09.3f %s [%s] %s" % (time.time() % 100000, source, level, message))

	def getuserbyauth(self, auth):
		return [u for u in self.users.values() if u.auth == auth.lower()]

	def getdb(self):
		"""Get a DB object. The object must be returned to the pool after us, using returndb()."""
		return self.dbs.pop()

	def returndb(self, db):
		self.dbs.append(db)

	#bind functions
	def hook(self, word, handler):
		try:
			self.msghandlers[word].append(handler)
		except:
			self.msghandlers[word] = [handler]
	def unhook(self, word, handler):
		if word in self.msghandlers and handler in self.msghandlers[word]:
			self.msghandlers[word].remove(handler)
	def hashook(self, word):
		return word in self.msghandlers and len(self.msghandlers[word]) != 0
	def gethook(self, word):
		return self.msghandlers[word]

	def hooknum(self, word, handler):
		try:
			self.numhandlers[word].append(handler)
		except:
			self.numhandlers[word] = [handler]
	def unhooknum(self, word, handler):
		if word in self.numhandlers and handler in self.numhandlers[word]:
			self.numhandlers[word].remove(handler)
	def hasnumhook(self, word):
		return word in self.numhandlers and len(self.numhandlers[word]) != 0
	def getnumhook(self, word):
		return self.numhandlers[word]

	def hookchan(self, chan, handler):
		try:
			self.chanhandlers[chan].append(handler)
		except:
			self.chanhandlers[chan] = [handler]
	def unhookchan(self, chan, handler):
		if chan in self.chanhandlers and handler in self.chanhandlers[chan]:
			self.chanhandlers[chan].remove(handler)
	def haschanhook(self, chan):
		return chan in self.chanhandlers and len(self.chanhandlers[chan]) != 0
	def getchanhook(self, chan):
		return self.chanhandlers[chan]


def dbsetup():
	main.db = None
	main.dbs = []
	for i in range(cfg.get('erebus', 'num_db_connections', 2)-1):
		main.dbs.append(MySQLdb.connect(host=cfg.dbhost, user=cfg.dbuser, passwd=cfg.dbpass, db=cfg.dbname, cursorclass=MySQLdb.cursors.DictCursor))
	main.db = MySQLdb.connect(host=cfg.dbhost, user=cfg.dbuser, passwd=cfg.dbpass, db=cfg.dbname, cursorclass=MySQLdb.cursors.DictCursor)

def setup():
	global cfg, main

	cfg = config.Config('bot.config')

	if cfg.getboolean('debug', 'gc'):
		gc.set_debug(gc.DEBUG_LEAK)

	pidfile = open(cfg.pidfile, 'w')
	pidfile.write(str(os.getpid()))
	pidfile.close()

	main = Erebus(cfg)
	dbsetup()

	autoloads = [mod for mod, yes in cfg.items('autoloads') if int(yes) == 1]
	for mod in autoloads:
		ctlmod.load(main, mod)

	c = main.query("SELECT nick, user, bind, authname, authpass FROM bots WHERE active = 1")
	if c:
		rows = c.fetchall()
		c.close()
		for row in rows:
			main.newbot(row['nick'], row['user'], row['bind'], row['authname'], row['authpass'], cfg.host, cfg.port, cfg.realname)
	main.connectall()

def loop():
	poready = main.poll()
	for fileno in poready:
		for line in main.fd(fileno).getdata():
			main.fd(fileno).parse(line)

if __name__ == '__main__':
	try: os.rename('logfile', 'oldlogs/%s' % (time.time()))
	except: pass
	sys.stdout = open('logfile', 'w', 1)
	sys.stderr = sys.stdout
	setup()
	while True: loop()
