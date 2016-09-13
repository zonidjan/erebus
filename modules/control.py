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


@lib.hook(needchan=False, glevel=lib.MANAGER)
def die(bot, user, chan, realtarget, *args):
	for botitem in bot.parent.bots.itervalues():
		for chan in botitem.chans:
			chan.fastmsg("Bot is restarting! %s" % ' '.join(args))
		bot.conn.send("QUIT :Restarting.")
	sys.exit(0)
	os._exit(0)

@lib.hook(needchan=False, glevel=lib.MANAGER)
@lib.argsEQ(1)
def modload(bot, user, chan, realtarget, *args):
	okay = ctlmod.load(bot.parent, args[0])
	if okay:
		bot.msg(user, "Loaded %s" % (args[0]))
	else:
		bot.msg(user, "Error loading %s: %r" % (args[0], okay))

@lib.hook(needchan=False, glevel=lib.MANAGER)
@lib.argsEQ(1)
def modunload(bot, user, chan, realtarget, *args):
	okay = ctlmod.unload(bot.parent, args[0])
	if okay:
		bot.msg(user, "Unloaded %s" % (args[0]))
	else:
		bot.msg(user, "Error unloading %s: %r" % (args[0], okay))

@lib.hook(needchan=False, glevel=lib.MANAGER)
@lib.argsEQ(1)
def modreload(bot, user, chan, realtarget, *args):
	okay = ctlmod.reloadmod(bot.parent, args[0])
	if okay:
		bot.msg(user, "Reloaded %s" % (args[0]))
	else:
		bot.msg(user, "Error occurred: %r" % (okay))

@lib.hook(needchan=False, glevel=lib.STAFF)
@lib.argsEQ(0)
def modlist(bot, user, chan, realtarget, *args):
	mods = ctlmod.modules
	for mod in mods.itervalues():
		bot.msg(user, "- %s %r" % (mod.__name__, mod))
	bot.msg(user, "Done.")

@lib.hook(cmd='whoami', needchan=False)
def whoami(bot, user, chan, realtarget, *args):
	if not user.isauthed():
		bot.msg(user, "You are not authed.")
		return

	fillers = {'auth': user.auth}
	fmt = "You are %(auth)s"

	if user.glevel >= 1:
		fillers['glevel'] = user.glevel
		fmt += " (global access: %(glevel)s)"
	else:
		fmt += " (not staff)"

	if chan is not None and chan.levelof(user.auth) >= 1:
		fillers['clevel'] = chan.levelof(user.auth)
		fmt += " (channel access: %(clevel)s)"
	else:
		fmt += " (not a channel user)"
	bot.msg(user, fmt % fillers)
