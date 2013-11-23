# preamble
import modlib
lib = modlib.modlib(__name__)
modstart = lib.modstart

#module code
@lib.hook('test')
def cmd_test(bot, user, chan, *args):
	bot.msg(chan, "You said: !test %s" % (' '.join([str(arg) for arg in args])))
