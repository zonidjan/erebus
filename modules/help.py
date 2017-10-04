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
	def __init__(self, cmd, syntax, shorthelp, admin, glevel, module, clevel):
		self.cmd = cmd
		self.syntax = syntax
		self.shorthelp = shorthelp
		self.admin = admin
		self.glevel = glevel
		self.module = module
		self.clevel = clevel

	def __cmp__(self, other):
		if self.glevel == other.glevel:
			return cmp(self.cmd, other.cmd)
		else:
			return cmp(self.glevel, other.glevel)


	def __str__(self):
		if self.admin:
			ret = "%-35s(%3s) - %-10s - " % (self.cmd+' '+self.syntax, self.glevel, self.module)
		else:
			ret = "%-40s - " % (self.cmd+' '+self.syntax)
		if self.clevel != 0:
			ret += "(%s) " % (lib.clevs[self.clevel])
		ret += str(self.shorthelp)
		return ret

def _mkhelp(level, func):
	lines = []
	if level >= func.reqglevel:
		lines.append(HelpLine(func.cmd[0], func.syntax, func.shorthelp, (level > 0), func.reqglevel, func.module, func.reqclevel))
		if len(func.cmd) > 1:
			for c in func.cmd[1:]:
				lines.append(HelpLine(c, "", "Alias of %s" % (func.cmd[0]), (level > 0), func.reqglevel, func.module, func.reqclevel))
	return lines

def _genhelp(bot, user, chan, realtarget, *args):
	module = None
	minlevel = -1
	maxlevel = 100
	filepath = bot.parent.cfg.get('help', 'path', default='./help/%d.txt')
	for arg in args:
		if arg.startswith("@"):
			module = arg[1:]
		elif arg.startswith("#") and user.glevel >= lib.ADMIN:
			minlevel = maxlevel = int(arg[1:])
		else:
			filepath = arg
			if minlevel != maxlevel:
				minlevel = maxlevel
	for level in range(minlevel, maxlevel+1):
		if '%d' in filepath:
			filename = filepath % (level)
		else:
			filename = filepath
		fo = open(filename, 'w')
		lines = []
		for func in helps.itervalues():
			if module is not None and func.module != module:
					continue
			lines += _mkhelp(level, func)
		for line in sorted(lines):
			fo.write(str(line)+"\n")
		fo.close()
	return True

@lib.hook(glevel=1, needchan=False)
@lib.help("[@<module>] [#<level>] [file]", "generates help file", "arguments are all optional and may be specified in any order", "default file: ./help/<level>.txt", "config as: [help]", "path = ./help/%d.txt")
def genhelp(bot, user, chan, realtarget, *args):
	try:
		_genhelp(bot, user, chan, realtarget, *args)
	except Exception as e:
		bot.msg(user, "Failed writing help. %s" % (e))
		return
	bot.msg(user, "Help written.")

@lib.hook(needchan=False)
@lib.help("<command>", "describes a command")
@lib.argsGE(1)
def help(bot, user, chan, realtarget, *args):
	cmd = str(' '.join(args)).lower()
	if cmd in cmds and user.glevel >= cmds[cmd].reqglevel:
		func = cmds[cmd]
		bot.slowmsg(user, str(HelpLine(func.cmd[0], func.syntax, func.shorthelp, (user.glevel > 0), func.reqglevel, func.module, func.reqclevel)))
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
		try:
			_genhelp(bot, user, chan, realtarget, *args)
		except: pass

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
	elif args[0].startswith("@"):
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
