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

# preamble
import modlib
lib = modlib.modlib(__name__)
modstart = lib.modstart
modstop = lib.modstop

# module setup
from fractions import Fraction

# module code
@lib.hook(needchan=False, wantchan=True)
@lib.help('<numerator>/<denominator>|<decimal>', 'reduces a fraction', 'you may supply a fraction in the form "1/2" or a decimal in the form ".5", "0.5", "5e-1", etc.')
def reduce(bot, user, chan, realtarget, *args):
	supplied_value = ''.join(args)
	try:
		frac = Fraction(supplied_value)
	except ValueError:
		return 'Invalid fraction supplied. You must supply a fraction in the form "1/2" or a decimal in the form ".5", "0.5", "5e-1", etc.'
	return "%s = %s" % (supplied_value, frac)
