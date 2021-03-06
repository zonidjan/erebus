# Erebus IRC bot - Author: Erebus Team
# vim: fileencoding=utf-8
# Various highly recommended "control" commands.
# This file is released into the public domain; see http://unlicense.org/

# module info
modinfo = {
	'author': 'Erebus Team',
	'license': 'public domain',
	'compatible': [0],
	'depends': [],
	'softdeps': ['help'],
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
@lib.help(None, "stops the bot")
def die(bot, user, chan, realtarget, *args):
	quitmsg = ' '.join(args)
	for botitem in bot.parent.bots.values():
		bot.conn.send("QUIT :Restarting. %s" % (quitmsg))
	sys.exit(0)
	os._exit(0)

@lib.hook(needchan=False, glevel=lib.MANAGER)
@lib.help("<mod>", "loads a module")
@lib.argsEQ(1)
def modload(bot, user, chan, realtarget, *args):
	okay = ctlmod.load(bot.parent, args[0])
	if okay:
		bot.msg(user, "Loaded %s" % (args[0]))
	else:
		bot.msg(user, "Error loading %s: %r" % (args[0], okay))

@lib.hook(needchan=False, glevel=lib.MANAGER)
@lib.help("<mod> [FORCE]", "unloads a module", "will refuse to unload a module which is depended on by others", "unless you specify FORCE.")
@lib.argsGE(1)
def modunload(bot, user, chan, realtarget, *args):
	if len(ctlmod.dependents[args[0]]) > 0:
		if len(args) == 1 or args[1].lower() != "force":
			bot.msg(user, "That module has dependents! Say MODUNLOAD %s FORCE to unload it and any dependents." % (args[0]))
			return
	okay = ctlmod.unload(bot.parent, args[0])
	if okay:
		bot.msg(user, "Unloaded %s" % (args[0]))
	else:
		bot.msg(user, "Error unloading %s: %r" % (args[0], okay))

@lib.hook(needchan=False, glevel=lib.MANAGER)
@lib.help("<mod>", "reloads a module")
@lib.argsEQ(1)
def modreload(bot, user, chan, realtarget, *args):
	okay = ctlmod.reloadmod(bot.parent, args[0])
	if okay:
		bot.msg(user, "Reloaded %s" % (args[0]))
	else:
		bot.msg(user, "Error occurred: %r" % (okay))

@lib.hook(needchan=False, glevel=lib.STAFF)
@lib.help(None, "list loaded modules")
@lib.argsEQ(0)
def modlist(bot, user, chan, realtarget, *args):
	mods = ctlmod.modules
	for modname, mod in mods.items():
		bot.msg(user, "- %s (%s) [%s]" % ((modname, mod.__file__, ', '.join(ctlmod.dependents[modname]))))
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

@lib.hook(needchan=False, wantchan=True)
@lib.help("<user|#auth>", "shows who someone is")
@lib.argsEQ(1)
def whois(bot, user, chan, realtarget, *args):
	name = args[0]
	if name.startswith("#"):
		target = bot.parent.User(name, name[1:])
	else:
		target = bot.parent.user(name, create=False)
	if target is None:
		return  "I don't know %s." % (args[0])
	else:
		return "%s is %s" % (args[0], _whois(target, chan, (user.glevel >= 1), (chan is not None and chan.levelof(user.auth) >= 1)))

@lib.hook(needchan=False, wantchan=True)
@lib.help(None, "shows who you are")
def whoami(bot, user, chan, realtarget, *args):
	return "You are %s" % (_whois(user, chan))

@lib.hook(needchan=False)
@lib.help(None, "tries to read your auth and access level again")
def auth(bot, user, chan, realtarget, *args):
	bot.msg(user, "Okay, give me a second.")
	bot.conn.send("WHO %s n%%ant,2" % (user))

@lib.hook(needchan=False, glevel=1)
@lib.help(None, "displays length of each msgqueue")
def qstat(bot, user, chan, realtarget, *args):
	bot.fastmsg(user, "Regular: %d -- Slow: %d" % (len(bot.msgqueue), len(bot.slowmsgqueue)))

@lib.hook(('qclear','cq','clearq','clearqueue'), needchan=False, glevel=lib.ADMIN)
@lib.help("[regular|slow]", "clears both or a specific msgqueue")
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

@lib.hook(needchan=False, wantchan=True, glevel=lib.ADMIN)
@lib.help("<nick> <message>", "inject a line as though it came from <nick>", "note that this injects lines, not commands", "ex: INJECT DimeCadmium !WHOAMI")
def inject(bot, user, chan, realtarget, *args):
	targetuser = bot.parent.user(args[0], create=False)
	if targetuser is None:
		bot.msg(user, "User is unknown.")
		return
	if targetuser.glevel > user.glevel:
		bot.msg(user, "That user has a higher access level than you.")
		return

	if chan is not None:
		bot.parsemsg(bot.parent.user(args[0], create=False), str(chan), ' '.join(args[1:]))
	else:
		bot.parsemsg(bot.parent.user(args[0], create=False), str(bot), ' '.join(args[1:]))
