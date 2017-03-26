# Erebus IRC bot - Author: Erebus Team
# !EVAL and !EXEC commands
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


def module(name):
	return lib.mod(name)

@lib.hook('eval', needchan=False, glevel=lib.MANAGER)
@lib.argsGE(1)
def cmd_eval(bot, user, chan, realtarget, *args):
	if chan is not None and realtarget == chan.name: replyto = chan
	else: replyto = user

	try: ret = eval(' '.join(args))
	except Exception: bot.msg(replyto, "Error: %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))
	else: bot.msg(replyto, "Done: %r" % (ret,))


@lib.hook('exec', needchan=False, glevel=lib.MANAGER)
@lib.argsGE(1)
def cmd_exec(bot, user, chan, realtarget, *args):
	if chan is not None and realtarget == chan.name: replyto = chan
	else: replyto = user

	try: exec ' '.join(args)
	except Exception: bot.msg(replyto, "Error: %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))
	else: bot.msg(replyto, "Done.")

@lib.hook('exception', glevel=lib.OWNER)
def cmd_exception(*args, **kwargs):
	raise Exception()
