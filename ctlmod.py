# Erebus IRC bot - Author: John Runyon
# module loading/unloading/tracking code

from __future__ import print_function

import sys, time
import modlib

if sys.version_info.major >= 3:
	from importlib import reload

modules = {}
dependents = {}
#dependents[modname] = [list of modules which depend on modname]

def isloaded(modname): return modname in modules
def modhas(modname, attname): return getattr(modules[modname], attname, None) is not None

def load(parent, modname, dependent=False):
	#wrapper to call _load and print return
	if dependent:
		print("(Loading dependency %s..." % (modname), end=' ')
	else:
		print("%09.3f [MOD] [?] Loading %s..." % (time.time() % 100000, modname), end=' ')
	modstatus = _load(parent, modname, dependent)
	if not modstatus:
		if dependent:
			print("failed: %s)" % (modstatus), end=' ')
		else:
			print("failed: %s." % (modstatus))
	elif modstatus == True:
		if dependent:
			print("OK)", end=' ')
		else:
			print("OK.")
	else:
		if dependent:
			print("OK: %s)" % (modstatus), end=' ')
		else:
			print("OK: %s." % (modstatus))
	return modstatus

def _load(parent, modname, dependent=False):
	successstatus = []
	if not isloaded(modname):
		try:
			mod = __import__('modules.'+modname, globals(), locals(), ['*'], 0)
			# ^ fromlist doesn't actually do anything(?) but it means we don't have to worry about this returning the top-level "modules" object
			reload(mod) #in case it's been previously loaded.
		except Exception as e:
			return modlib.error(e)


		if not hasattr(mod, 'modinfo'):
			return modlib.error('no modinfo')

		if parent.APIVERSION not in mod.modinfo['compatible']:
			return modlib.error('API-incompatible')

		modules[modname] = mod
		dependents[modname] = []

		for dep in mod.modinfo['depends']:
			if bool(int(parent.cfg.get('autoloads', dep, default=1))):
				if dep not in modules:
					depret = load(parent, dep, dependent=True)
					if depret is not None and not depret:
						return depret
			else:
				return modlib.error("dependent %s disabled" % (dep))
			dependents[dep].append(modname)

		for dep in mod.modinfo['softdeps']:
			if bool(int(parent.cfg.get('autoloads', dep, default=1))):
				if dep not in modules:
					depret = load(parent, dep, dependent=True)
					if depret is not None:
						if not depret:
							successstatus.append("softdep %s failed" % (dep))
			else:
				successstatus.append("softdep %s disabled" % (dep))
			#swallow errors loading - softdeps are preferred, not required


		ret = mod.modstart(parent)
		if ret is None:
			ret = True
		if not ret:
			del modules[modname]
			del dependents[modname]
			for dep in mod.modinfo['depends']:
				dependents[dep].remove(modname)

		successstatus = ';'.join(successstatus)
		if len(successstatus) > 0 and ret:
			if ret == True:
				return successstatus
			else:
				return "%s (%s)" % (ret, successstatus)
		else:
			return ret
	else: #if not isloaded...else:
		return modlib.error('already loaded')

def unload(parent, modname):
	if isloaded(modname):
		for dependent in dependents[modname]:
			unload(parent, dependent)
		for dep in modules[modname].modinfo['depends']:
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
