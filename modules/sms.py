# Erebus IRC bot - Author: Erebus Team
# simple module example
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
from twilio.rest import TwilioRestClient

def client(bot):
	return TwilioRestClient(
		bot.parent.cfg.get('sms', 'account_sid'),
		bot.parent.cfg.get('sms', 'auth_token')
	)


#@lib.hook(needchan=False, glevel=lib.MANAGER)
def reply(bot, user, chan, realtarget, *args):
	pass

@lib.hook(('sms','w'), needchan=False, glevel=lib.OWNER)
def sms(bot, user, chan, realtarget, *args):
	number = "+%s" % (args[0])
	message = ' '.join(args[1:])
	client(bot).messages.create(body=message, to=number, from_=bot.parent.cfg.get('sms', 'mynumber'))
	bot.msg(user, "Sent message to %s" % (number))
