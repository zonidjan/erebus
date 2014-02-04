# Erebus IRC bot - Author: Conny Sjoblom
# Twitch URL Checker
# This file is released into the public domain; see http://unlicense.org/

# module info
modinfo = {
	'author': 'Conny Sjoblom',
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
hostmask_regex = re.compile('^(.*)!(.*)@(.*)$')
url_regex = re.compile('(http|ftp|https):\/\/([\w\-_]+(?:(?:\.[\w\-_]+)+))([\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?')
def parser_hostmask(hostmask):
	if isinstance(hostmask, dict):
		return hostmask

	nick = None
	user = None
	host = None

	if hostmask is not None:
		match = hostmask_regex.match(hostmask)

		if not match:
			nick = hostmask
		else:
			nick = match.group(1)
			user = match.group(2)
			host = match.group(3)

	return {
		'nick': nick,
		'user': user,
		'host': host
	}

@lib.hooknum("PRIVMSG")
def privmsg_hook(bot, line):
	sender = parser_hostmask(line[1:line.find(' ')])

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
				bot.msg(line.split()[2], 'Twitch: %s (%s)' % (twitch[0]['channel']['status'], twitch[0]['channel']['meta_game']))
			except:
				bot.msg(line.split()[2], 'Twitch: Channel offline.')
