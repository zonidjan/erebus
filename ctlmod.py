# Erebus IRC bot - Author: John Runyon
# module loading/unloading/tracking code

import sys, time
import modlib

modules = {}
dependents = {}

def isloaded(modname): return modname in modules
def modhas(modname, attname): return getattr(modules[modname], attname, None) is not None

def load(parent, modname, dependent=False):
	#wrapper to call _load and print return
	if dependent:
		print "Loading dependency %s..." % (modname),
	else:
		print "%05.3f [MOD] [#] Loading %s... " % (time.time() % 100000, modname),
	modstatus = _load(parent, modname, dependent)
	if not modstatus:
		print str(modstatus)
	elif modstatus == True:
		if dependent:
			print "OK. ",
		else:
			print "OK."
	else:
		print modstatus
	return modstatus

def _load(parent, modname, dependent=False):
	if not isloaded(modname):
		sys.path.insert(0, 'modules')
		try:
			mod = __import__(modname)
			reload(mod) #in case it's been previously loaded.
		except BaseException as e: #we don't want even sys.exit() to crash us (in case of malicious module) so use BaseException
			return modlib.error(e)
		finally:
			del sys.path[0] #remove ./modules from path, in case there's a name conflict


		if not hasattr(mod, 'modinfo'):
			return modlib.error('no modinfo')

		if parent.APIVERSION not in mod.modinfo['compatible']:
			return modlib.error('API-incompatible')

		modules[modname] = mod
		dependents[modname] = []

		for dep in mod.modinfo['depends']:
			if dep not in modules:
				depret = load(parent, dep, dependent=True)
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
		ret = modules[modname].modstop(parent)
		del modules[modname]
		return ret
	else:
		return modlib.error('already unloaded')

def reloadmod(parent, modname):
	if isloaded(modname):
		if modhas(modname, 'modrestart'): modules[modname].modrestart(parent)
		else: modules[modname].modstop(parent)

		try:
			reload(modules[modname])
		except BaseException as e:
			return modlib.error(e)

		if modhas(modname, 'modrestarted'): ret = modules[modname].modrestarted(parent)
		else: ret = modules[modname].modstart(parent)

		return ret
	else:
		return load(parent, modname)


def loadall(parent, modlist):
	for m in modlist: load(parent, m)
def unloadall(parent, modlist):
	for m in modlist: unload(parent, m)
def reloadall(parent, modlist):
	for m in modlist: reloadmod(parent, m)

sys.path.append('modules')
