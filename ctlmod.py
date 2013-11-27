import sys

modules = {}

def isloaded(modname): return modname in modules
def modhas(modname, attname): return getattr(self.modules[modname], attname, None) is not None

def load(parent, modname):
	if not isloaded(modname):
		mod = __import__(modname)
		modules[modname] = mod
		ret = mod.modstart(parent)
		if not ret:
			del modules[modname]
		return ret
	else:
		return -1

def unload(parent, modname):
	if isloaded(modname):
		self.modules[modname].modstop(parent)
	else:
		return -1

def reloadmod(parent, modname):
	if isloaded(modname):
		if modhas(modname, 'modrestart'): self.modules[modname].modrestart(parent)
		else: self.modules[modname].modstop(parent)

		reload(self.modules[modname])

		if modhas(modname, 'modrestarted'): self.modules[modname].modrestarted(parent)
		else: self.modules[modname].modstart(parent)

	else:
		load(parent, modname)

def loadall(parent, modlist):
	for m in modlist: load(parent, m)
def unloadall(parent, modlist):
	for m in modlist: unload(parent, m)
def reloadall(parent, modlist):
	for m in modlist: reloadmod(parent, m)

sys.path.append('modules')
