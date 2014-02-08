# Erebus IRC bot - Author: Erebus Team
# URL Checker
# This file is released into the public domain; see http://unlicense.org/

# module info
modinfo = {
	'author': 'Erebus Team',
	'license': 'public domain',
	'compatible': [1], # compatible module API versions
	'depends': [], # other modules required to work properly?
}

# http://embed.ly/tools/generator

# preamble
import modlib
lib = modlib.modlib(__name__)
modstart = lib.modstart
modstop = lib.modstop

# module code
import re, json, urllib2, urlparse, HTMLParser
from BeautifulSoup import BeautifulSoup

hostmask_regex = re.compile(r'^(.*)!(.*)@(.*)$')

spotify_regex = (
	re.compile(r'spotify:(?P<type>\w+):(?P<track_id>\w{22})'),
	re.compile(r'http://open.spotify.com/(?P<type>\w+)/(?P<track_id>\w{22})')
)
youtube_regex = (
	re.compile(r'https?://(?:www\.)?youtube\.com/watch\?[a-zA-Z0-9=&_\-]+'),
)
twitch_regex = (
	re.compile('(http|ftp|https):\/\/([\w\-_]+(?:(?:\.[\w\-_]+)+))([\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?'), #TODO
)

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

	chan = line.split()[2]

	if 'open.spotify.com' in line or 'spotify:' in line:
		for r in spotify_regex:
			for sptype, track in r.findall(linetx):
				bot.msg(chan, gotspotify(sptype, track))

	elif 'youtube.com' in line or 'youtu.be' in line:
		print "got youtube!"
		for r in youtube_regex:
			for url in r.findall(linetx):
				bot.msg(chan, gotyoutube(url))

	elif 'twitch.tv' in line: pass #TODO fix twitch

	else: pass #TODO generic <title> checker


def gotspotify(type, track):
	url = 'http://ws.spotify.com/lookup/1/?uri=spotify:%s:%s' % (type, track)
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
	
		return 'Track: %s - %s / %s %s:%.2d %2d%%' % (artist_name, name, album_name, minutes, seconds, popularity)
	
	elif lookup_type == 'album':
		album_name = soup.find('album').find('name').string
		artist_name = soup.find('artist').find('name').string
		released = soup.find('released').string
		return 'Album: %s - %s - %s' % (artist_name, album_name, released)
	
	else:
		return 'Unsupported type.'

def gotyoutube(url):
	url_data = urlparse.urlparse(url)
	query = urlparse.parse_qs(url_data.query)
	video = query["v"][0]
	api_url = 'http://gdata.youtube.com/feeds/api/videos/%s?alt=json&v=2' % video
	try:
		respdata = urllib2.urlopen(api_url).read()
		video_info = json.loads(respdata)

		title = video_info['entry']['title']["$t"]
		author = video_info['entry']['author'][0]['name']['$t']

		return "Youtube: %s (%s)" % (title, author)
	except:
		pass


def gottwitch(url):
	return ""
	#FIXME:
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

