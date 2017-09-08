# Erebus IRC bot - Author: Erebus Team
# This file is released into the public domain; see http://unlicense.org/

# module info
modinfo = {
	'author': 'Erebus Team',
	'license': 'public domain',
	'compatible': [1,2],
	'depends': [],
	'softdeps': ['help'],
}

# preamble
import modlib
lib = modlib.modlib(__name__)
modstart = lib.modstart
modstop = lib.modstop

# module code
@lib.hook(clevel=lib.OP)
@lib.help('<message>', 'sends message to channel')
@lib.argsGE(1)
def cmsg(bot, user, chan, realtarget, *args):
	chan.msg(' '.join(args))


def _getbot(bot, user, chan, realtarget, *args):
	target = None
	if args[0][0] == "#":
		target = bot.parent.channel(args[0])
		print "target = %s" % (target)
	if target is not None:
		sendbot = target.bot
		print "bot = %s" % (sendbot)
	else:
		target = args[0]
		sendbot = bot.parent.randbot()
		print "bot = random"
	return (target, sendbot)

@lib.hook(glevel=lib.STAFF, needchan=False)
@lib.help('<target> <message>', 'send message to target')
@lib.argsGE(2)
def msg(bot, user, chan, realtarget, *args):
	target, sendbot = _getbot(bot, user, chan, realtarget, *args)
	sendbot.msg(target, ' '.join(args[1:]))

@lib.hook(glevel=lib.STAFF, needchan=False)
@lib.help('<target> <message>', 'send message to target as PRIVMSG')
def pmsg(bot, user, chan, realtarget, *args):
	target, sendbot = _getbot(bot, user, chan, realtarget, *args)
	sendbot.conn.send("PRIVMSG %s :%s" % (args[0], ' '.join(args[1:])))

@lib.hook()
def moo(bot, user, chan, realtarget, *args):
	for i in ['          .=     ,        =.\n', "  _  _   /'/    )\\,/,/(_   \\ \\\n", '   `//-.|  (  ,\\\\)\\//\\)\\/_  ) |\n', "   //___\\   `\\\\\\/\\\\/\\/\\\\///'  /\n", ',-"~`-._ `"--\'_   `"""`  _ \\`\'"~-,_\n', '\\       `-.  \'_`.      .\'_` \\ ,-"~`/\n', " `.__.-'`/   (-\\        /-) |-.__,'\n", '   ||   |     \\O)  /^\\ (O/  |\n', '   `\\\\  |         /   `\\    /\n', '     \\\\  \\       /      `\\ /\n', "      `\\\\ `-.  /' .---.--.\\\n", "        `\\\\/`~(, '()      ('\n", '         /(O) \\\\   _,.-.,_)\n', "        //  \\\\ `\\'`      /\n", '       / |  ||   `""""~"`\n', "     /'  |__||\n", '           `o\n']:
		bot.fastmsg(chan, i.rstrip("\n"))
