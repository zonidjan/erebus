# Erebus IRC bot - Author: Erebus Team
# URL Checker
# This file is released into the public domain; see http://unlicense.org/

# module info
modinfo = {
	'author': 'Erebus Team',
	'license': 'public domain',
	'compatible': [1,2],
	'depends': [],
	'softdeps': [],
}

# http://embed.ly/tools/generator

# preamble
import modlib
lib = modlib.modlib(__name__)
modstart = lib.modstart
modstop = lib.modstop

# module code
import re, urllib2, urlparse, json, HTMLParser
from BeautifulSoup import BeautifulSoup

html_parser = HTMLParser.HTMLParser()

hostmask_regex = re.compile(r'^(.*)!(.*)@(.*)$')
url_regex = re.compile(r'((?:https?://|spotify:)[^\s]+)')
spotify_regex = (
	re.compile(r'spotify:(?P<type>\w+):(?P<track_id>\w{22})'),
	re.compile(r'https?://open.spotify.com/(?P<type>\w+)/(?P<track_id>\w{22})')
)
youtube_regex = (
	re.compile(r'https?://(?:www\.)?youtube\.com/watch\?[a-zA-Z0-9=&_\-]+'),
)
twitch_regex = (
	re.compile(r'https?:\/\/(?:www\.)?twitch.tv\/([A-Za-z0-9]*)'),
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

class SmartRedirectHandler(urllib2.HTTPRedirectHandler):
	def http_error_301(self, req, fp, code, msg, headers):
		result = urllib2.HTTPRedirectHandler.http_error_301(
				self, req, fp, code, msg, headers)
		result.status = code
		return result

	def http_error_302(self, req, fp, code, msg, headers):
		result = urllib2.HTTPRedirectHandler.http_error_302(
				self, req, fp, code, msg, headers)
		result.status = code
		return result

@lib.hooknum("PRIVMSG")
def privmsg_hook(bot, textline):
	user = parser_hostmask(textline[1:textline.find(' ')])
	chan = textline.split()[2]

	try:
		line = textline.split(None, 3)[3][1:]
	except IndexError:
		line = ''

	for match in url_regex.findall(line):
		if match:
			if 'open.spotify.com' in match or 'spotify:' in match:
				for r in spotify_regex:
					for sptype, track in r.findall(match):
						bot.msg(chan, gotspotify(sptype, track))

			elif 'youtube.com' in match or 'youtu.be' in match:
				for r in youtube_regex:
					for url in r.findall(match):
						bot.msg(chan, gotyoutube(url))

			elif 'twitch.tv' in match:
				for r in twitch_regex:
					for uri in r.findall(match):
						bot.msg(chan, gottwitch(uri))

			else:
				bot.msg(chan, goturl(match))

def unescape(line):
	return html_parser.unescape(line)

def gotspotify(type, track):
	url = 'http://ws.spotify.com/lookup/1/?uri=spotify:%s:%s' % (type, track)
	xml = urllib2.urlopen(url).read()
	soup = BeautifulSoup(xml, convertEntities=BeautifulSoup.HTML_ENTITIES)
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

		return unescape('Track: %s - %s / %s %s:%.2d %2d%%' % (artist_name, name, album_name, minutes, seconds, popularity))

	elif lookup_type == 'album':
		album_name = soup.find('album').find('name').string
		artist_name = soup.find('artist').find('name').string
		released = soup.find('released').string
		return unescape('Album: %s - %s - %s' % (artist_name, album_name, released))

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

		return unescape("Youtube: %s (%s)" % (title, author))
	except:
		pass

def gottwitch(uri):
		url = 'http://api.justin.tv/api/stream/list.json?channel=%s' % uri.split('/')[0]
		respdata = urllib2.urlopen(url).read()
		twitch = json.loads(respdata)
		try:
			return unescape('Twitch: %s (%s playing %s)' % (twitch[0]['channel']['status'], twitch[0]['channel']['login'], twitch[0]['channel']['meta_game']))
		except:
			return 'Twitch: Channel offline.'

def goturl(url):
	request = urllib2.Request(url)
	opener = urllib2.build_opener(SmartRedirectHandler())
	try:
		soup = BeautifulSoup(opener.open(request, timeout=2))
		return unescape('Title: %s' % (soup.title.string))
	except:
		return 'Invalid URL/Timeout'
