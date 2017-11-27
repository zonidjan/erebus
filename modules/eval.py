# Erebus IRC bot - Author: Erebus Team
# !EVAL and !EXEC commands
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

@lib.hook('eval', needchan=False, wantchan=True, glevel=lib.OWNER)
@lib.help("<python>", "eval")
@lib.argsGE(1)
def cmd_eval(bot, user, chan, realtarget, *args):
	if chan is not None: replyto = chan
	else: replyto = user

	try: ret = eval(' '.join(args))
	except Exception: bot.msg(replyto, "Error: %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))
	else: bot.msg(replyto, "Done: %r" % (ret,))


@lib.hook('exec', needchan=False, wantchan=True, glevel=lib.OWNER)
@lib.help("<python>", "exec")
@lib.argsGE(1)
def cmd_exec(bot, user, chan, realtarget, *args):
	if chan is not None: replyto = chan
	else: replyto = user

	try: exec ' '.join(args)
	except Exception: bot.msg(replyto, "Error: %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))
	else: bot.msg(replyto, "Done.")

@lib.hook('exception', needchan=False, glevel=lib.OWNER)
@lib.help(None, "cause an exception")
def cmd_exception(*args, **kwargs):
	raise Exception()
