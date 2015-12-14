# Erebus IRC bot - Author: Erebus Team
# Various highly recommended "control" commands.
# This file is released into the public domain; see http://unlicense.org/

# module info
modinfo = {
	'author': 'Erebus Team',
	'license': 'public domain',
	'compatible': [1],
	'depends': [],
}

# preamble
import modlib
lib = modlib.modlib(__name__)
modstart = lib.modstart
modstop = lib.modstop

# module code
import sys
import ctlmod


@lib.hook('die', needchan=False, glevel=lib.MANAGER)
def cmd_die(bot, user, chan, realtarget, *args):
	sys.exit(0)
	os._exit(0)

@lib.hook('modload', needchan=False, glevel=lib.MANAGER)
@lib.argsEQ(1)
def cmd_modload(bot, user, chan, realtarget, *args):
	okay = ctlmod.load(bot.parent, args[0])
	if okay:
		bot.msg(user, "Loaded %s" % (args[0]))
	else:
		bot.msg(user, "Error loading %s: %r" % (args[0], okay))

@lib.hook('modunload', needchan=False, glevel=lib.MANAGER)
@lib.argsEQ(1)
def cmd_modunload(bot, user, chan, realtarget, *args):
	okay = ctlmod.unload(bot.parent, args[0])
	if okay:
		bot.msg(user, "Unloaded %s" % (args[0]))
	else:
		bot.msg(user, "Error unloading %s: %r" % (args[0], okay))

@lib.hook('modreload', needchan=False, glevel=lib.MANAGER)
@lib.argsEQ(1)
def cmd_modreload(bot, user, chan, realtarget, *args):
	okay = ctlmod.reloadmod(bot.parent, args[0])
	if okay:
		bot.msg(user, "Reloaded %s" % (args[0]))
	else:
		bot.msg(user, "Error occurred: %r" % (okay))

@lib.hook('modlist', needchan=False, glevel=lib.STAFF)
@lib.argsEQ(0)
def cmd_modlist(bot, user, chan, realtarget, *args):
	mods = ctlmod.modules
	for mod in mods.itervalues():
		bot.msg(user, "- %s %r" % (mod.__name__, mod))
	bot.msg(user, "Done.")
