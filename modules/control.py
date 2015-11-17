# Erebus IRC bot - Author: Erebus Team
# !EVAL and !EXEC commands
# This file is released into the public domain; see http://unlicense.org/

# module info
modinfo = {
	'author': 'Erebus Team',
	'license': 'public domain',
	'compatible': [1],
	'depends': [],
}

# preamble
import modlib
lib = modlib.modlib(__name__)
modstart = lib.modstart
modstop = lib.modstop

# module code
import sys
import ctlmod


@lib.hook('die', needchan=False, glevel=lib.MANAGER)
def cmd_die(bot, user, chan, realtarget, *args):
	sys.exit(0)
	os._exit(0)
