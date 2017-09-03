# Erebus IRC bot - Author: Erebus Team
# help module
# This file is released into the public domain; see http://unlicense.org/

# module info
modinfo = {
	'author': 'Erebus Team',
	'license': 'public domain',
	'compatible': [1,2],
	'depends': [],
	'softdeps': [],
}

# preamble
import modlib
lib = modlib.modlib(__name__)
modstart = lib.modstart
modstop = lib.modstop

# module code
import os.path
helps = {}
cmds  = {}

# ! this is part of this module's API, called from modlib.help()
def reghelp(func, *args, **kwargs):
	syntax = None
	shorthelp = None
	longhelps = []

	if len(args) > 0:
		syntax = args[0]
		if len(args) > 1:
			shorthelp = args[1]
			if len(args) > 2:
				longhelps = args[2:]

	if 'syntax' in kwargs:
		syntax = kwargs['syntax']
	if 'shorthelp' in kwargs:
		shorthelp = kwargs['shorthelp']
	if 'longhelps' in kwargs:
		longhelps = kwargs['longhelps']

	if syntax is None: syntax = ""
	if shorthelp is None: shorthelp = ""

	func.syntax = syntax
	func.shorthelp = shorthelp
	func.longhelps = longhelps
	helps[func] = func
	for c in func.cmd:
		cmds[c] = func

def dereghelp(func, *args, **kwargs):
	for c in func.cmd:
		del cmds[c]
	del helps[func]

class HelpLine(object):
	def __init__(self, cmd, syntax, shorthelp, admin, level, module):
		self.cmd = cmd
		self.syntax = syntax
		self.shorthelp = shorthelp
		self.admin = admin
		self.level = level
		self.module = module

	def __cmp__(self, other):
		if self.level == other.level:
			return cmp(self.cmd, other.cmd)
		else:
			return cmp(self.level, other.level)


	def __str__(self):
		if self.admin:
			return "%-35s(%3s) - %-10s - %-50s" % (self.cmd+' '+self.syntax, self.level, self.module, self.shorthelp)
		else:
			return "%-40s - %-50s" % (self.cmd+' '+self.syntax, self.shorthelp)

def _mkhelp(level, func):
	lines = []
	if level >= func.reqglevel:
		lines.append(HelpLine(func.cmd[0], func.syntax, func.shorthelp, (level > 0), func.reqglevel, func.module))
		if len(func.cmd) > 1:
			for c in func.cmd[1:]:
				lines.append(HelpLine(c, "", "Alias of %s" % (func.cmd[0]), (level > 0), func.reqglevel, func.module))
	return lines

def _genhelp(bot, user, chan, realtarget, *args):
	try:
		filepath = bot.parent.cfg.get('help', 'path', default='./help/%d.txt')
		for level in range(-1, 101):
			filename = filepath % (level)
			fo = open(filename, 'w')
			lines = []
			for func in helps.itervalues():
				lines += _mkhelp(level, func)
			for line in sorted(lines):
				fo.write(str(line)+"\n")
	except Exception as e:
		return e
	return True

@lib.hook(glevel=1, needchan=False)
@lib.help(None, "generates help file", "default path: ./help/<level>.txt", "config as: [help]", "path = ./help/%d.txt")
#TODO: use args... "[@<module>] [#<level>] [<file>]"
def genhelp(bot, user, chan, realtarget, *args):
	ret = _genhelp(bot, user, chan, realtarget, *args)
	if not isinstance(ret, BaseException):
		bot.msg(user, "Help written.")
	else:
		bot.msg(user, "Failed writing help. %s" % (ret))

@lib.hook(needchan=False)
@lib.help("<command>", "describes a command")
@lib.argsGE(1)
def help(bot, user, chan, realtarget, *args):
	cmd = str(' '.join(args)).lower()
	if cmd in cmds and user.glevel >= cmds[cmd].reqglevel:
		func = cmds[cmd]
		bot.slowmsg(user, str(HelpLine(func.cmd[0], func.syntax, func.shorthelp, (user.glevel > 0), func.reqglevel, func.module)))
		for line in func.longhelps:
			bot.slowmsg(user, "  %s" % (line))
		bot.slowmsg(user, "End of help for %s." % (func.cmd[0]))
		if len(func.cmd) > 1:
			bot.slowmsg(user, "  Aliases: %s" % (' '.join(func.cmd[1:])))
	else:
		bot.slowmsg(user, "No help found for %s" % (cmd))

@lib.hook(needchan=False)
@lib.help(None, "provides command list")
def showcommands(bot, user, chan, realtarget, *args):
	if bool(int(bot.parent.cfg.get('help', 'autogen', default=0))):
		_genhelp(bot, user, chan, realtarget, *args)
	url = bot.parent.cfg.get('help', 'url', default=None)
	if url is None:
		try:
			import urllib2
			myip = urllib2.urlopen("https://api.ipify.org").read()
			url = "http://%s/help/%%d.txt (maybe)" % (myip)
		except: url = None
	if url is not None:
		url = url % (user.glevel)
		bot.msg(user, "Help is at: %s" % (url))
	else:
		bot.msg(user, "I don't know where help is. Sorry. Contact my owner.")

"""#DISABLED
@lib.hook(needchan=False)
@lib.help('[@<module>|<command>]', 'lists commands or describes a command', 'with @<module>, lists all commands in <module>')
def help(bot, user, chan, realtarget, *args):
	if len(args) == 0: # list commands
		lines = []
		for func in helps.itervalues():
			lines += _mkhelp(user, func)
		for line in sorted(lines):
			bot.slowmsg(user, str(line))
		bot.slowmsg(user, "End of command listing.")
	elif args[0][0] == "@":
		lines = []
		mod = args[0][1:].lower()
		for func in helps.itervalues():
			if func.module == mod:
				lines += _mkhelp(user, func)
		for line in sorted(lines):
			bot.slowmsg(user, str(line))
		bot.slowmsg(user, "End of command listing.")
	else: # help for a specific command/topic
		cmd = str(' '.join(args)).lower()
		if cmd in cmds and user.glevel >= cmds[cmd].reqglevel:
			func = cmds[cmd]
			bot.slowmsg(user, str(HelpLine(func.cmd[0], func.syntax, func.shorthelp, (user.glevel > 0), func.reqglevel, func.module)))
			for line in func.longhelps:
				bot.slowmsg(user, "  %s" % (line))
			bot.slowmsg(user, "End of help for %s." % (func.cmd[0]))

			if len(func.cmd) > 1:
				bot.slowmsg(user, "  Aliases: %s" % (' '.join(func.cmd[1:])))
		else:
			bot.slowmsg(user, "No help found for %s" % (cmd))
"""
pass
