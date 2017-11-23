# Erebus IRC bot - Author: Erebus Team
# module for 's/regex/replacement/' style correction
# see for usage examples: https://github.com/zonidjan/erebus/commit/d7e9802778477f1faa26a03078cb1b3c018a5e5c
# This file is released into the public domain; see http://unlicense.org/

# module info
modinfo = {
	'author': 'Erebus Team',
	'license': 'public domain',
	'compatible': [2], # compatible module API versions
	'depends': [], # other modules required to work properly?
	'softdeps': [], # modules which are preferred but not required
}

# preamble
import modlib
lib = modlib.modlib(__name__)
modstart = lib.modstart
modstop = lib.modstop

# module code
import re
from collections import namedtuple
re_findsub = re.compile(r"s(.)(?P<search>[^\1]+)\1(?P<replace>[^\1]+)\1(?P<global>g)?;?")
Line = namedtuple('Line', ['sender', 'msg'])
lastline = {}
@lib.hooknum("PRIVMSG")
def privmsg_hook(bot, line):
	pieces = line.split(None, 3)
	fromnick = pieces[0][1:].split('!')[0]
	chan = pieces[2]
	msg = pieces[3][1:]
	mo = re_findsub.match(msg)
	if mo:
		print lastline[chan]
		print mo.groupdict()
		if mo.group('global') is not None:
			count = 0 # unlimited
		else:
			count = 1 # only first
		try:
			newline = re.sub(mo.group('search'), mo.group('replace'), lastline[chan].msg, count)
		except Exception as e: print e; return # ignore it if it doesn't work
		print newline
		if newline != lastline[chan].msg:
			if lastline[chan].sender == fromnick:
				bot.msg(chan, "<%s> %s" % (lastline[chan].sender, newline))
			else:
				bot.msg(chan, "%s: <%s> %s" % (fromnick, lastline[chan].sender, newline))
	else:
		lastline[chan] = Line(sender=fromnick, msg=msg)
