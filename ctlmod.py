# Erebus IRC bot - Author: John Runyon
# module loading/unloading/tracking code

import sys
import modlib

modules = {}
dependents = {}

def isloaded(modname): return modname in modules
def modhas(modname, attname): return getattr(self.modules[modname], attname, None) is not None

def load(parent, modname):
	if not isloaded(modname):
		mod = __import__(modname)
		reload(mod)

		if 1 not in mod.modinfo['compatible']:
			return modlib.error('API-incompatible')

		modules[modname] = mod
		dependents[modname] = []

		for dep in mod.modinfo['depends']:
			if dep not in modules:
				depret = load(parent, dep)
				if not depret:
					return
			dependents[dep].append(modname)


		ret = mod.modstart(parent)
		if ret is not None and not ret:
			del modules[modname]
			del dependents[modname]
			for dep in mod.modinfo['depends']:
				dependents[dep].remove(modname)
		return ret
	else: #if not isloaded...else:
		return modlib.error('already loaded')

def unload(parent, modname):
	if isloaded(modname):
		for dependent in dependents[modname]:
			unload(parent, dependent)
		for dep in dependents[modname]:
			dependents[dep].remove(modname)
		self.modules[modname].modstop(parent)
	else:
		return modlib.error('already unloaded')

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
