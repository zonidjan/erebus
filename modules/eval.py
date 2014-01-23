# Erebus IRC bot - Author: John Runyon
# !EVAL and !EXEC commands

# module info
modinfo = {
	'author': 'John Runyon (DimeCadmium)',
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


@lib.hook('eval', needchan=False, glevel=lib.MANAGER)
@lib.argsGE(1)
def cmd_eval(bot, user, chan, realtarget, *args):
	if chan is not None: replyto = chan
	else: replyto = user

	try: ret = eval(' '.join(args))
	except: bot.msg(replyto, "Error (%s): %s" % (sys.exc_info()[0], sys.exc_info()[1]))
	else: bot.msg(replyto, "Done: %r" % (ret))


@lib.hook('exec', needchan=False, glevel=lib.MANAGER)
@lib.argsGE(1)
def cmd_exec(bot, user, chan, realtarget, *args):
	if chan is not None: replyto = chan
	else: replyto = user

	try: exec ' '.join(args)
	except: bot.msg(replyto, "Error: %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))
	else: bot.msg(replyto, "Done.")
