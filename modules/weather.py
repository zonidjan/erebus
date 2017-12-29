# Erebus IRC bot - Author: Erebus Team
# weather module
# This file is released into the public domain; see http://unlicense.org/

# module info
modinfo = {
	'author': 'Erebus Team',
	'license': 'public domain',
	'compatible': [0],
	'depends': ['userinfo'],
	'softdeps': ['help'],
}

# preamble
import modlib
lib = modlib.modlib(__name__)
modstart = lib.modstart
modstop = lib.modstop

# module code
import json, urllib, time, rfc822

def location(person, default=None): return lib.mod('userinfo')._get(person, 'location', default=None)

def _weather(place):
	if place is not None:
		weather = json.load(urllib.urlopen('http://api.wunderground.com/api/8670e6d2e69ff3c7/conditions/q/%s.json' % (place)))
		if lib.parent.cfg.getboolean('debug', 'weather'):
			lib.parent.log('*', "?", repr(weather))
		if 'response' in weather:
			if 'error' in weather['response']:
				return "Error from Wunderground: %s" % (weather['response']['error']['description'])
			if 'results' in weather['response']:
				return "That search term is ambiguous. Please be more specific."

		current = weather['current_observation']
		measuredat = rfc822.parsedate(current['observation_time_rfc822']) # parsedate_tz returns a 10-tuple which strftime DOESN'T ACCEPT
		measuredatTZ = current['local_tz_short']
		loc = current['observation_location']
		if loc['city'] == "" or loc['state'] == "": loc = current['display_location']
		return u"Weather in %(location)s: As of %(time)s %(tz)s, %(conditions)s, %(cel)s\u00B0C (%(far)s\u00B0F) (feels like %(flcel)s\u00B0C (%(flfar)s\u00B0F)). Wind %(wind)s. %(link)s" % {
			'location': loc['full'],
			'time': time.strftime("%a %H:%M", measuredat), 'tz': measuredatTZ,
			'conditions': current['weather'],
			'cel': current['temp_c'], 'far': current['temp_f'],
			'flcel': current['feelslike_c'], 'flfar': current['feelslike_f'],
			'wind': current['wind_string'],
			'link': current['forecast_url'],
		}
	else:
		return "I don't know where to look! Try %sSETINFO LOCATION <your location>" % (lib.parent.trigger)

@lib.hook(('weather','w'), needchan=False, wantchan=True)
@lib.help('[<location>]', 'show weather for your location')
def weather(bot, user, chan, realtarget, *args):
	if chan is None:
		chan = user
	if len(args) == 0:
		place = location(user)
	else:
		place = ' '.join(args)
	bot.msg(chan, _weather(place))

@lib.hook(('weatheruser','wu'))
@lib.help('<user>', 'show weather for <user>\'s location')
def wu(bot, user, chan, realtarget, *args):
	bot.msg(chan, _weather(location(' '.join(args))))
