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
