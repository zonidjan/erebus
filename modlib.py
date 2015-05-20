# Erebus IRC bot - Author: John Runyon
# module helper functions, see modules/modtest.py for usage
# This file is released into the public domain; see http://unlicense.org/

class error(object):
	def __init__(self, desc):
		self.errormsg = desc
	def __nonzero__(self):
		return False #object will test to False
	def __repr__(self):
		return '<modlib.error %r>' % self.errormsg
	def __str__(self):
		return self.errormsg

class modlib(object):
	# default (global) access levels
	MANAGER = 100
	ADMIN = 75
	STAFF = 50
	AUTHED = 0
	ANYONE = -1

	# (channel) access levels
	OWNER = 5
	MASTER = 4
	OP = 3
	VOICE = 2
	KNOWN = 1
	PUBLIC = 0 #anyone (use glevel to control auth-needed)

	# messages
	WRONGARGS = "Wrong number of arguments."

	def __init__(self, name):
		self.hooks = {}
		self.numhooks = {}
		self.chanhooks = {}
		self.parent = None

		self.name = name

	def modstart(self, parent):
		self.parent = parent
		for cmd, func in self.hooks.iteritems():
			self.parent.hook(cmd, func)
		for num, func in self.numhooks.iteritems():
			self.parent.hooknum(num, func)
		for chan, func in self.chanhooks.iteritems():
			self.parent.hookchan(chan, func)
		return True
	def modstop(self, parent):
		for cmd, func in self.hooks.iteritems():
			self.parent.unhook(cmd, func)
		for num, func in self.numhooks.iteritems():
			self.parent.unhooknum(num, func)
		for chan, func in self.chanhooks.iteritems():
			self.parent.unhookchan(chan, func)
		return True

	def hooknum(self, num):
		def realhook(func):
			self.numhooks[num] = func
			if self.parent is not None:
				self.parent.hooknum(num, func)
			return func
		return realhook

	def hookchan(self, chan, glevel=ANYONE, clevel=PUBLIC):
		def realhook(func):
			self.chanhooks[chan] = func
			if self.parent is not None:
				self.parent.hookchan(chan, func)
			return func
		return realhook

	def hook(self, cmd, needchan=True, glevel=ANYONE, clevel=PUBLIC):
		def realhook(func):
			func.needchan = needchan
			func.reqglevel = glevel
			func.reqclevel = clevel

			self.hooks[cmd] = func
			if self.parent is not None:
				self.parent.hook(cmd, func)
			return func
		return realhook

	def argsEQ(self, num):
		def realhook(func):
			def checkargs(bot, user, chan, realtarget, *args):
				if len(args) == num:
					return func(bot, user, chan, realtarget, *args)
				else:
					bot.msg(user, self.WRONGARGS)
			return checkargs
		return realhook

	def argsGE(self, num):
		def realhook(func):
			def checkargs(bot, user, chan, realtarget, *args):
				if len(args) >= num:
					return func(bot, user, chan, realtarget, *args)
				else:
					bot.msg(user, self.WRONGARGS)
			return checkargs
		return realhook
