# Erebus IRC bot - Author: Erebus Team
# This file is released into the public domain; see http://unlicense.org/

# module info
modinfo = {
	'author': 'Erebus Team',
	'license': 'public domain',
	'compatible': [2],
	'depends': [],
	'softdeps': ['help'],
}

# preamble
import modlib
lib = modlib.modlib(__name__)
modstart = lib.modstart
modstop = lib.modstop

# module code
import time

@lib.hook(clevel=lib.OP)
@lib.help('<message>', 'sends message to channel')
@lib.argsGE(1)
def cmsg(bot, user, chan, realtarget, *args):
	chan.msg(' '.join(args))


def _getbot(bot, user, chan, realtarget, *args):
	target = None
	if args[0].startswith("#"):
		target = bot.parent.channel(args[0])
	if target is not None:
		sendbot = target.bot
	else:
		target = args[0]
		sendbot = bot.parent.randbot()
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

@lib.hook(glevel=lib.MANAGER, needchan=False)
@lib.argsEQ(1)
def moo(bot, user, chan, realtarget, *args):
	lines= ['          .=     ,        =.', "  _  _   /'/    )\\,/,/(_   \\ \\", '   `//-.|  (  ,\\\\)\\//\\)\\/_  ) |', "   //___\\   `\\\\\\/\\\\/\\/\\\\///'  /", ',-"~`-._ `"--\'_   `"""`  _ \\`\'"~-,_', '\\       `-.  \'_`.      .\'_` \\ ,-"~`/', " `.__.-'`/   (-\\        /-) |-.__,'", '   ||   |     \\O)  /^\\ (O/  |', '   `\\\\  |         /   `\\    /', '     \\\\  \\       /      `\\ /', "      `\\\\ `-.  /' .---.--.\\", "        `\\\\/`~(, '()      ('", '         /(O) \\\\   _,.-.,_)', "        //  \\\\ `\\'`      /", '       / |  ||   `""""~"`', "     /'  |__||", '           `o']
	for i in range(len(lines)):
		sender = bot.parent.bots.values()[i%len(bot.parent.bots.values())]
		mylen = len(sender.nick)
		padding = 15-mylen
		sender.fastmsg(args[0], " "*padding + lines[i])
		time.sleep(0.1)
