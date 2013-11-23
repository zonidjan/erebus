class modlib(object):
	hooks = {}
	parent = None

	def __init__(self, name):
		self.name = name

	def modstart(self, parent):
		self.parent = parent
		for cmd, func in self.hooks.iteritems():
			self.parent.hook(cmd, func)

	def hook(self, cmd):
		def realhook(func):
			self.hooks[cmd] = func
			if self.parent is not None:
				self.parent.hook(cmd, func)
			return func
		return realhook
