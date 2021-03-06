# Erebus IRC bot - Author: Erebus Team
# vim: fileencoding=utf-8
# resource-usage module
# This file is released into the public domain; see http://unlicense.org/

# module info
modinfo = {
	'author': 'Erebus Team',
	'license': 'public domain',
	'compatible': [0],
	'depends': [],
	'softdeps': ['help'],
}

# preamble
import modlib
lib = modlib.modlib(__name__)
modstart = lib.modstart
modstop = lib.modstop

# module code
import resource, time

@lib.hook(needchan=False, wantchan=True, glevel=lib.MANAGER)
@lib.help(None, "show RAM usage")
def ram(bot, user, chan, realtarget, *args):
	if chan is not None: replyto = chan
	else: replyto = user

	try:
		res = resource.getrusage(resource.RUSAGE_BOTH)
	except:
		res = resource.getrusage(resource.RUSAGE_SELF)

	bot.fastmsg(replyto, "Memory usage (MiB): %r" % (res.ru_maxrss/1024.0))

@lib.hook(needchan=False, wantchan=True, glevel=lib.MANAGER)
@lib.help(None, "show resource usage")
def resources(bot, user, chan, realtarget, *args):
	if chan is not None: replyto = chan
	else: replyto = user

	uptime = time.time() - bot.parent.starttime
	m, s = divmod(uptime, 60)
	h, m = divmod(m, 60)
	d, h = divmod(h, 24)
	try:
		res = resource.getrusage(resource.RUSAGE_BOTH)
	except:
		res = resource.getrusage(resource.RUSAGE_SELF)

	bot.slowmsg(replyto, "Resource usage:")
	for i, v in (
		('uptime (s)', "%d (%d days %02d:%02d:%02d)" % (uptime, d, h, m, s)),
		('utime (s)', res.ru_utime),
		('stime (s)', res.ru_stime),
		('memory (MiB)', (res.ru_maxrss/1024.0)),
		('I/O (blocks)', res.ru_inblock+res.ru_oublock),
		('page faults', res.ru_majflt),
		('signals', res.ru_nsignals),
		('context switches (voluntary)', res.ru_nvcsw),
		('context switches (involuntary)', res.ru_nivcsw),
	):
		bot.slowmsg(replyto, "- %s: %s" % (i, v))
	bot.slowmsg(replyto, "EOL.")
