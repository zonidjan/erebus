# Erebus IRC bot - Author: Erebus Team
# Spotify URL Checker
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
from BeautifulSoup import BeautifulSoup

checkfor = "spotify"
hostmask_regex = re.compile('^(.*)!(.*)@(.*)$')
spotify_regex = ( re.compile(r'spotify:(?P<type>\w+):(?P<track_id>\w{22})'),
									re.compile(r'http://open.spotify.com/(?P<type>\w+)/(?P<track_id>\w{22})') )
spotify_gateway = 'http://ws.spotify.com/lookup/1/'
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

	for r in spotify_regex:
		for type, track in r.findall(linetx):
			url = '%s?uri=spotify:%s:%s' % (spotify_gateway, type, track)
			xml = urllib2.urlopen(url).read()
			soup = BeautifulSoup(xml)
			lookup_type = soup.contents[2].name

			if lookup_type == 'track':
				name = soup.find('name').string
				album_name = soup.find('album').find('name').string
				artist_name = soup.find('artist').find('name').string
				popularity = soup.find('popularity')
				if popularity:
					popularity = float(popularity.string)*100
				length = float(soup.find('length').string)
				minutes = int(length)/60
				seconds =  int(length)%60

				bot.msg(line.split()[2], 'Track: %s - %s / %s %s:%.2d %2d%%' %(artist_name, name,
								album_name, minutes, seconds, popularity))

			elif lookup_type == 'album':
				album_name = soup.find('album').find('name').string
				artist_name = soup.find('artist').find('name').string
				released = soup.find('released').string
				bot.msg(line.split()[2], 'Album: %s - %s - %s' %(artist_name, album_name, released))

			else:
				bot.notice(sender['nick'], "Unsupported type.")
