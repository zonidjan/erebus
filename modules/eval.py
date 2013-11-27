# preamble
import modlib
lib = modlib.modlib(__name__)
modstart = lib.modstart
modstop = lib.modstop

#module code
import sys


@lib.hook('eval')
def cmd_eval(bot, user, chan, *args):
	try: ret = eval(' '.join(args))
	except: bot.msg(chan, "Error (%s): %s" % (sys.exc_info()[0], sys.exc_info()[1]))
	else: bot.msg(chan, "Done: %r" % (ret))


@lib.hook('exec')
def cmd_exec(bot, user, chan, *args):
	try: exec ' '.join(args)
	except: bot.msg(chan, "Error: %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))
	else: bot.msg(chan, "Done.")
