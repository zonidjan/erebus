# Erebus IRC bot - Author: Erebus Team
# simple module example
# This file is released into the public domain; see http://unlicense.org/

# module info
modinfo = {
	'author': 'Erebus Team',
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
@lib.hook(needchan=False) #since no cmd= is provided, defaults to function name
@lib.help('<args>', 'tells you what you said')
def test(bot, user, chan, realtarget, *args):
	if chan is not None and realtarget == chan.name: replyto = chan
	else: replyto = user

	bot.msg(replyto, "You said: %s" % (' '.join([str(arg) for arg in args])))

@lib.hook(('foo', 'bar'), needchan=False) #hooks !foo and !bar as aliases
@lib.help(None, 'replies with nonsense.', "it's a very non-sensical command", "more lines")
def foobar(bot, user, chan, realtarget, *args):
	bot.msg(user, "Foo bar baz.")

@lib.hook()
@lib.help(None, 'a command that does nothing but requires you specify a channel')
def needchan(bot, user, chan, realtarget, *args):
	bot.msg(user, "You did it!")
