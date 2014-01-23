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
	OWNER = -10
	MASTER = -8 #master is {-8,-9}
	OP = -5 #op is {-5,-6,-7}
	VOICE = -4
	KNOWN = -3
	PUBLIC = -2 #anyone (use glevel to control auth-needed)

	# messages
	WRONGARGS = "Wrong number of arguments."

	def __init__(self, name):
		self.hooks = {}
		self.parent = None

		self.name = name

	def modstart(self, parent):
		self.parent = parent
		for cmd, func in self.hooks.iteritems():
			self.parent.hook(cmd, func)
		return True
	def modstop(self, parent):
		for cmd, func in self.hooks.iteritems():
			self.parent.unhook(cmd)
		return True

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
