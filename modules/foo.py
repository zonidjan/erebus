# Erebus IRC bot - Author: John Runyon
# simple module example
# This file is released into the public domain; see http://unlicense.org/

# module info
modinfo = {
	'author': 'John Runyon (DimeCadmium)',
	'license': 'public domain',
	'compatible': [1], # compatible module API versions
	'depends': [], # other modules required to work properly?
}

# preamble
import modlib
lib = modlib.modlib(__name__)
modstart = lib.modstart
modstop = lib.modstop

# module code
@lib.hook('test')
def cmd_test(bot, user, chan, realtarget, *args):
	bot.msg(chan, "You said: %s" % (' '.join([str(arg) for arg in args])))
