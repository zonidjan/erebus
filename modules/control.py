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
import sys, os
import ctlmod
from collections import deque


@lib.hook(('die','restart'), needchan=False, glevel=lib.MANAGER)
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

def _whois(user, chan, showglevel=True, showclevel=True):
	if not user.isauthed():
		return "not authed."

	fillers = {'auth': user.auth}
	fmt = "%(auth)s"

	if showglevel and user.glevel >= 1:
			fillers['glevel'] = user.glevel
			fmt += " (global access: %(glevel)s)"
	elif user.glevel >= 1:
		fmt += " (staff)"
	else:
		fmt += " (not staff)"

	if showclevel and chan is not None:
		if chan.levelof(user.auth) >= 1:
			fillers['clevel'] = chan.levelof(user.auth)
			fmt += " (channel access: %(clevel)s)"
		else:
			fmt += " (not a channel user)"
	return fmt % fillers

@lib.hook(needchan=False)
@lib.argsEQ(1)
def whois(bot, user, chan, realtarget, *args):
	target = bot.parent.user(args[0], create=False)
	if target is None:
		bot.msg(user, "I don't know %s." % (args[0]))
	else:
		bot.msg(user, "%s is %s" % (args[0], _whois(target, chan, (user.glevel >= 1), (chan is not None and chan.levelof(user.auth) >= 1))))

@lib.hook(needchan=False)
def whoami(bot, user, chan, realtarget, *args):
	bot.msg(user, "You are %s" % (_whois(user, chan)))

@lib.hook(needchan=False, glevel=1)
def qstat(bot, user, chan, realtarget, *args):
	bot.fastmsg(user, "Regular: %d -- Slow: %d" % (len(bot.msgqueue), len(bot.slowmsgqueue)))

@lib.hook(needchan=False, glevel=lib.ADMIN)
def qclear(bot, user, chan, realtarget, *args):
	if len(args) == 0:
		bot.msgqueue = deque()
		bot.slowmsgqueue = deque()
		bot.fastmsg(user, "Cleared both msgqueues.")
	else:
		if args[0] == 'regular':
			bot.msgqueue = deque()
		elif args[0] == 'slow':
			bot.slowmsgqueue = deque()
		else:
			bot.fastmsg(user, "Syntax: QCLEAR [regular|slow]")
			return #short-circuit
		bot.fastmsg(user, "Cleared that msgqueue.")
