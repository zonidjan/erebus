# Erebus IRC bot - Author: Erebus Team
# vim: fileencoding=utf-8
# simple module example
# This file is released into the public domain; see http://unlicense.org/

# module info
modinfo = {
	'author': 'Erebus Team',
	'license': 'public domain',
	'compatible': [0], # compatible module API versions
	'depends': [], # other modules required to work properly?
	'softdeps': ['help'], # modules which are preferred but not required
}
# note: softdeps will be loaded before this module, IF not disabled in the configuration (autoload.module = 0) (and if it exists)
# however, if it is disabled it will be silently ignored, and if it is unloaded at runtime it won't cause this one to unload.
#
# basically, softdeps are things this module will use if available, but does not require (no errors will occur if it's not loaded)
# for example, @lib.help() will attempt to use the help module, but swallow errors if it is not loaded

# preamble
import modlib
lib = modlib.modlib(__name__)
modstart = lib.modstart
modstop = lib.modstop

# module code
@lib.hook(needchan=False, wantchan=True) #since no cmd= is provided, defaults to function name
@lib.help('<args>', 'tells you what you said')
def test(bot, user, chan, realtarget, *args):
	if chan is not None: replyto = chan
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

@lib.hook(needchan=False, wantchan=True)
@lib.help(None, 'a command which will consume a channel if given')
def wantchan(bot, user, chan, realtarget, *args):
	if chan is not None:
		bot.msg(user, "Channel provided: %s" % (chan))
	else:
		bot.msg(user, "No channel provided")
