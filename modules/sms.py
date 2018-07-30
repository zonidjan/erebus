# Erebus IRC bot - Author: Erebus Team
# vim: fileencoding=utf-8
# twilio sms module
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
from twilio.rest import TwilioRestClient

def client(bot):
	return TwilioRestClient(
		bot.parent.cfg.get('sms', 'account_sid'),
		bot.parent.cfg.get('sms', 'auth_token')
	)


@lib.hook(needchan=False, glevel=lib.MANAGER)
def reply(bot, user, chan, realtarget, *args):
	raise NotImplementedError

@lib.hook(('sms','w'), needchan=False, glevel=lib.OWNER)
@lib.help("<number> <message>", "send an SMS")
def sms(bot, user, chan, realtarget, *args):
	number = "+%s" % (args[0])
	message = ' '.join(args[1:])
	client(bot).messages.create(body=message, to=number, from_=bot.parent.cfg.get('sms', 'mynumber'))
	bot.msg(user, "Sent message to %s" % (number))
