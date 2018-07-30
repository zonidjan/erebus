# Erebus IRC bot - Author: Erebus Team
# vim: fileencoding=utf-8
# staff list module
# This file is released into the public domain; see http://unlicense.org/

# module info
modinfo = {
	'author': 'Erebus Team',
	'license': 'public domain',
	'compatible': [0], # compatible module API versions
	'depends': [], # other modules required to work properly?
	'softdeps': ['help'], # modules which are preferred but not required
}

# preamble
import modlib
lib = modlib.modlib(__name__)
modstart = lib.modstart
modstop = lib.modstop

# module code
def _getnicks(auth):
	nicks = [x.nick for x in lib.parent.getuserbyauth(auth)]
	if len(nicks) == 0:
		return 'not online'
	else:
		return ', '.join(nicks)

@lib.hook(needchan=False)
@lib.help(None, 'lists staff')
@lib.argsEQ(0)
def stafflist(bot, user, chan, realtarget, *args):
	c = lib.parent.query("SELECT auth, level FROM users WHERE level > %s", (lib.parent.cfg.get('stafflist', 'minstafflevel', default=lib.KNOWN),))
	if c:
		staffs = c.fetchall()
		c.close()
		if len(staffs) > 0:
			if user.glevel > lib.KNOWN:
				response = ["#%s (%s, %s)" % (i['auth'], _getnicks(i['auth']), i['level']) for i in staffs]
			else:
				response = ["#%s (%s)" % (i['auth'], _getnicks(i['auth'])) for i in staffs]
			user.msg("Staff listing: %s" % (', '.join(response)))
