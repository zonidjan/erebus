# Erebus IRC bot - Author: Erebus Team
# chanop commands
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
import sys
import ctlmod


def module(name):
	return lib.mod(name)

def _kick(bot, user, chan, realtarget, *args):
	people = []
	if args[0].startswith("#"):
		people = bot.parent.getuserbyauth(args[0][1:])
	else:
		people = [args[0]]

	if len(args) > 1:
		reason = ' '.join(args[1:])
	else:
		reason = "Commanded"

	for person in people:
		bot.conn.send("KICK %s %s :%s" % (chan, person, reason))
	return len(people)

@lib.hook(None, clevel=lib.OP)
@lib.help("<nick|#auth> [<reason>]", "kick <nick>, or all using <#auth>")
@lib.argsGE(1)
def kick(bot, user, chan, realtarget, *args):
	number = _kick(bot, user, chan, realtarget, *args)
	bot.msg(user, "Done. Kicked %d people." % (number))

@lib.hook(None, clevel=lib.OP)
@lib.help("<nick> [<reason>]", "kick all using the auth of <nick>")
@lib.argsGE(1)
def kickall(bot, user, chan, realtarget, *args):
	auth = bot.parent.user(args[0]).auth
	if auth is not None:
		number = _kick(bot, user, chan, realtarget, "#"+bot.parent.user(args[0]).auth, *args[1:])
		bot.msg(user, "Done. Kicked %d people." % (number))
	else:
		bot.msg(user, "I don't know that person's auth.")

@lib.hook(None, clevel=lib.OP)
@lib.help("<nick> [...]", "kicks multiple nicks.")
def kickeach(bot, user, chan, realtarget, *args):
	number = 0
	for person in args:
		number += _kick(bot, user, chan, realtarget, person)
	bot.msg(user, "Done. Kicked %d people." % (number))



def _mode(bot, chan, flag, letter, nicks):
	bot.conn.send("MODE %s %s%s %s" % (chan, flag, letter*len(nicks), ' '.join(nicks)))

@lib.hook(None, clevel=lib.OP)
@lib.help("[<nick>] [...]", "ops yourself or <nick>s")
def op(bot, user, chan, realtarget, *args):
	if len(args) == 0: args = (user.nick,)
	_mode(bot, chan, "+", "o", args)
	bot.msg(user, "Opped.")

@lib.hook(None, clevel=lib.OP)
@lib.help("[<nick>] [...]", "deops yourself or <nick>s")
def deop(bot, user, chan, realtarget, *args):
	if len(args) == 0: args = (user.nick,)
	_mode(bot, chan, "-", "o", args)
	bot.msg(user, "Deopped.")

@lib.hook(None, clevel=lib.OP)
@lib.help("[<nick>] [...]", "voices yourself or <nick>s")
def voice(bot, user, chan, realtarget, *args):
	if len(args) == 0: args = (user.nick,)
	_mode(bot, chan, "+", "v", args)
	bot.msg(user, "Voiced.")

@lib.hook(None, clevel=lib.OP)
@lib.help("[<nick>] [...]", "devoices yourself or <nick>s")
def devoice(bot, user, chan, realtarget, *args):
	if len(args) == 0: args = (user.nick,)
	_mode(bot, chan, "-", "v", args)
	bot.msg(user, "Devoiced.")

