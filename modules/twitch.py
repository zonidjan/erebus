# Erebus IRC bot - Author: Erebus Team
# Twitch URL Checker
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
import re
import urllib2
import json

checkfor = "twitch"
url_regex = re.compile('(http|ftp|https):\/\/([\w\-_]+(?:(?:\.[\w\-_]+)+))([\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?')

@lib.hooknum("PRIVMSG")
def privmsg_hook(bot, line):
	try:
		linetx = line.split(None, 3)[3][1:]
	except IndexError:
		linetx = ''

	if checkfor not in line:
		return # doesn't concern us

	for p, h, c in url_regex.findall(linetx):
		if checkfor in h:
			url = 'http://api.justin.tv/api/stream/list.json?channel=%s' % c[1:]
			respdata = urllib2.urlopen(url).read()
			twitch = json.loads(respdata)
			try:
				bot.msg(line.split()[2], 'Twitch: %s (%s playing %s)' % (twitch[0]['channel']['status'], twitch[0]['channel']['login'], twitch[0]['channel']['meta_game']))
			except:
				bot.msg(line.split()[2], 'Twitch: Channel offline.')
