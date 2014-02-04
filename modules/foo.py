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
@lib.hook('test', needchan=False)
def cmd_gtest(bot, user, chan, realtarget, *args):
	print type(chan), repr(chan), str(chan)

	if chan is not None: replyto = chan
	else: replyto = user

	bot.msg(replyto, "You said: %s" % (' '.join([str(arg) for arg in args])))
