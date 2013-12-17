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
	#access levels
	MANAGER = 3
	ADMIN = 2
	STAFF = 1
	AUTHED = 0
	ANYONE = -1

	def __init__(self, name):
		self.hooks = {}
		self.parent = None

		self.name = name

	def modstart(self, parent):
		self.parent = parent
		for cmd, func in self.hooks.iteritems():
			self.parent.hook(cmd, func)
	def modstop(self, parent):
		for cmd, func in self.hooks.iteritems():
			self.parent.unhook(cmd, func)

	def hook(self, cmd):
		def realhook(func):
			self.hooks[cmd] = func
			if self.parent is not None:
				self.parent.hook(cmd, func)
			return func
		return realhook
