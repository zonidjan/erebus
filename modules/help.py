# Erebus IRC bot - Author: Erebus Team
# help module
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
helps = {}
cmds  = {}

# ! this is part of this module's API, called from modlib.help()
# this function only handles the command name and aliases - the rest is passed directly to _reghelp()
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
		del cmds[cmd]
	del helps[func]

class HelpLine(object):
	def __init__(self, cmd, syntax, shorthelp, level=0):
		self.cmd = cmd
		self.syntax = syntax
		self.shorthelp = shorthelp
		self.level = level

	def __cmp__(self, other):
		if self.level == other.level:
			return cmp(self.cmd, other.cmd)
		else:
			return cmp(self.level, other.level)


	def __str__(self):
		if self.level <= 0:
			return "%-40s - %-50s" % (self.cmd+' '+self.syntax, self.shorthelp)
		else:
			return "%-35s(%3s) - %-50s" % (self.cmd+' '+self.syntax, self.level, self.shorthelp)

@lib.hook(needchan=False)
@lib.help('[<command>]', 'lists commands or describes a command')
def help(bot, user, chan, realtarget, *args): #TODO add ordering - by access level, then alphabetic?
	if len(args) == 0: # list commands
		lines = []
		for func in helps.itervalues():
			if user.glevel >= func.reqglevel:
				if func.reqglevel <= 0:
					lines.append(HelpLine(func.cmd[0], func.syntax, func.shorthelp))
#					bot.slowmsg(user, "%-40s - %-50s" % (func.cmd[0]+' '+func.syntax, func.shorthelp))
				else:
					lines.append(HelpLine(func.cmd[0], func.syntax, func.shorthelp, func.reqglevel))
#					bot.slowmsg(user, "%-40s - %-50s (%5s)" % (func.cmd[0]+' '+func.syntax, func.shorthelp, func.reqglevel))
				if len(func.cmd) > 1:
					for c in func.cmd[1:]:
						lines.append(HelpLine(c, "", "Alias of %s" % (func.cmd[0]), func.reqglevel))
#						bot.slowmsg(user, "%-40s - Alias of %s" % (c, func.cmd[0]))
		for line in sorted(lines):
			bot.slowmsg(user, str(line))
	else: # help for a specific command/topic
		cmd = str(' '.join(args))
		if cmd in cmds and user.glevel >= cmds[cmd].reqglevel:
			func = cmds[cmd]
			if func.reqglevel <= 0:
				bot.slowmsg(user, "%-40s - %-50s" % (func.cmd[0]+' '+func.syntax, func.shorthelp))
			else:
				bot.slowmsg(user, "%-40s - %-50s (%5s)" % (func.cmd[0]+' '+func.syntax, func.shorthelp, func.reqglevel))
			for line in func.longhelps:
				bot.slowmsg(user, "  %s" % (line))

			if len(func.cmd) > 1:
				bot.slowmsg(user, "  Aliases: %s" % (' '.join(func.cmd[1:])))
		else:
			bot.slowmsg(user, "No help found for %s" % (cmd))
