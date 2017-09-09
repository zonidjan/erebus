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
		return str(self.errormsg)

class modlib(object):
	# default (global) access levels
	OWNER   = 100
	MANAGER =  99
	ADMIN   =  75
	STAFF   =  50
	AUTHED  =   0
	ANYONE  =  -1
	IGNORED =  -2

	# (channel) access levels
	COWNER  =   5
	MASTER  =   4
	OP      =   3
	VOICE   =   2
	KNOWN   =   1
	PUBLIC  =   0 #anyone (use glevel to control auth-needed)
	BANNED  =  -1
	#         [   0         1        2     3         4        5    -1]
	clevs   = [None, 'Friend', 'Voice', 'Op', 'Master', 'Owner', None]

	# messages
	WRONGARGS = "Wrong number of arguments."

	def __init__(self, name):
		self.hooks = {}
		self.numhooks = {}
		self.chanhooks = {}
		self.helps = []
		self.parent = None

		self.name = (name.split("."))[-1]

	def modstart(self, parent):
		#modstart can return a few things...
		# None: unspecified success
		# False: unspecified error
		# modlib.error (or anything else False-y): specified error
		# True: unspecified success
		# non-empty string (or anything else True-y): specified success
		#"specified" values will be printed. unspecified values will result in "OK" or "failed"
		self.parent = parent
		for cmd, func in self.hooks.iteritems():
			self.parent.hook(cmd, func)
			self.parent.hook("%s.%s" % (self.name, cmd), func)
		for num, func in self.numhooks.iteritems():
			self.parent.hooknum(num, func)
		for chan, func in self.chanhooks.iteritems():
			self.parent.hookchan(chan, func)

		for func, args, kwargs in self.helps:
			try:
				self.mod('help').reghelp(func, *args, **kwargs)
			except:
				pass
		return True
	def modstop(self, parent):
		for cmd, func in self.hooks.iteritems():
			parent.unhook(cmd, func)
			parent.unhook("%s.%s" % (self.name, cmd), func)
		for num, func in self.numhooks.iteritems():
			parent.unhooknum(num, func)
		for chan, func in self.chanhooks.iteritems():
			parent.unhookchan(chan, func)

		for func, args, kwargs in self.helps:
			try:
				self.mod('help').dereghelp(func, *args, **kwargs)
			except:
				pass
		return True

	def hooknum(self, num):
		def realhook(func):
			self.numhooks[str(num)] = func
			if self.parent is not None:
				self.parent.hooknum(str(num), func)
			return func
		return realhook

	def hookchan(self, chan, glevel=ANYONE, clevel=PUBLIC):
		def realhook(func):
			self.chanhooks[chan] = func
			if self.parent is not None:
				self.parent.hookchan(chan, func)
			return func
		return realhook

	def hook(self, cmd=None, needchan=True, glevel=ANYONE, clevel=PUBLIC):
		_cmd = cmd #save this since it gets wiped out...
		def realhook(func):
			cmd = _cmd #...and restore it
			if cmd is None:
				cmd = func.__name__ # default to function name
			if isinstance(cmd, basestring):
				cmd = (cmd,)

			func.needchan = needchan
			func.reqglevel = glevel
			func.reqclevel = clevel
			func.cmd = cmd
			func.module = func.__module__.split('.')[1]

			for c in cmd:
				self.hooks[c] = func
				if self.parent is not None:
					self.parent.hook(c, func)
					self.parent.hook("%s.%s" % (self.name, c), func)
			return func
		return realhook

	def mod(self, modname):
		if self.parent is not None:
			return self.parent.module(modname)
		else:
			return error('unknown parent')

	def argsEQ(self, num):
		def realhook(func):
			def checkargs(bot, user, chan, realtarget, *args):
				if len(args) == num:
					return func(bot, user, chan, realtarget, *args)
				else:
					bot.msg(user, self.WRONGARGS)
			checkargs.__name__ = func.__name__
			checkargs.__module__ = func.__module__
			return checkargs
		return realhook

	def argsGE(self, num):
		def realhook(func):
			def checkargs(bot, user, chan, realtarget, *args):
				if len(args) >= num:
					return func(bot, user, chan, realtarget, *args)
				else:
					bot.msg(user, self.WRONGARGS)
			checkargs.__name__ = func.__name__
			checkargs.__module__ = func.__module__
			return checkargs
		return realhook

	def help(self, *args, **kwargs):
		"""help(syntax, shorthelp, longhelp?, more lines longhelp?, cmd=...?)
		Example:
		help("<user> <pass>", "login")
			^ Help will only be one line. Command name determined based on function name.
		help("<user> <level>", "add a user", cmd=("adduser", "useradd"))
			^ Help will be listed under ADDUSER; USERADD will say "alias for adduser"
		help(None, "do stuff", "This command is really complicated.")
			^ Command takes no args. Short description (in overall HELP listing) is "do stuff".
			Long description (HELP <command>) will say "<command> - do stuff", newline, "This command is really complicated."
		"""
		def realhook(func):
			if self.parent is not None:
				try:
					self.mod('help').reghelp(func, *args, **kwargs)
				except:
					pass
			self.helps.append((func,args,kwargs))
			return func
		return realhook
