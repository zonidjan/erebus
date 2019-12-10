# Erebus IRC bot - Author: Erebus Team
# vim: fileencoding=utf-8
# URL Checker
# This file is released into the public domain; see http://unlicense.org/

# module info
modinfo = {
	'author': 'Erebus Team',
	'license': 'public domain',
	'compatible': [0],
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
import sys
if sys.version_info.major < 3:
	import urllib2
	import urlparse
	import HTMLParser
	from BeautifulSoup import BeautifulSoup
else:
	import urllib.request as urllib2
	import urllib.parse as urlparse
	import html.parser as HTMLParser
	from bs4 import BeautifulSoup

import re, json, datetime

html_parser = HTMLParser.HTMLParser()

hostmask_regex = re.compile(r'^(.*)!(.*)@(.*)$')

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

def process_line(line):
	responses = []
	num_found = 0
	limit = lib.parent.cfg.getint('urls', 'limit', 2)
	for action, group, prefix in regexes:
		for regex in group:
			for match in regex.findall(line):
				if match:
					num_found += 1
					if num_found > limit:
						return responses
					resp = action(match)
					if resp is not None:
						responses.append("%s: %s" % (prefix, action(match)))
	return responses

@lib.hooknum("PRIVMSG")
def privmsg_hook(bot, textline):
	user = parser_hostmask(textline[1:textline.find(' ')])
	chan = textline.split()[2]

	try:
		line = textline.split(None, 3)[3][1:]
	except IndexError:
		line = ''

	responses = process_line(line)
	if len(responses) > 0:
		if lib.parent.cfg.getboolean('urls', 'multiline'):
			for r in responses:
				bot.msg(chan, r, True)
		else:
			bot.msg(chan, ' | '.join(responses), True)

def unescape(line):
	return re.sub('\s+', ' ', html_parser.unescape(line))

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
		seconds = int(length)%60

		return unescape('Track: %s - %s / %s %s:%.2d %2d%%' % (artist_name, name, album_name, minutes, seconds, popularity))

	elif lookup_type == 'album':
		album_name = soup.find('album').find('name').string
		artist_name = soup.find('artist').find('name').string
		released = soup.find('released').string
		return unescape('Album: %s - %s - %s' % (artist_name, album_name, released))

	else:
		return 'Unsupported type.'

def _yt_duration(s):
	mo = re.match(r'P(\d+D)?T(\d+H)?(\d+M)?(\d+S)?', s)
	pcs = [x for x in mo.groups() if x]
	return ''.join(pcs).lower()
def _yt_date(s, f):
	mo = re.match(r'(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})\.(\d+)Z', s)
	return datetime.datetime(*(int(x) for x in mo.groups())).strftime(f)
def _yt_round(n):
	n = float(n)
	if n >= 10**12:
		return '%.1ft' % (n/10**12)
	elif n >= 10**9:
		return '%.1fb' % (n/10**9)
	elif n >= 10**6:
		return '%.1fm' % (n/10**6)
	elif n >= 10**3:
		return '%.1fk' % (n/10**3)
	else:
		return int(n)

def gotyoutube(url):
	url_data = urlparse.urlparse(url)
	query = urlparse.parse_qs(url_data.query)
	video = query["v"][0]
	api_url = 'https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id=%s&key=%s' % (video, lib.parent.cfg.get('urls', 'api_key'))
	try:
		respdata = urllib2.urlopen(api_url).read()
		v = json.loads(respdata)
		v = v['items'][0]

		return unescape(lib.parent.cfg.get('urls', 'yt_format', "\002%(author)s\002: \037%(title)s\037 [%(duration)s, uploaded %(uploaded)s, %(views)s v/%(likes)s l/%(dislikes)s d]") % {
			'title': v['snippet']['title'],
			'author': v['snippet']['channelTitle'],
			'duration': _yt_duration(v['contentDetails']['duration']),
			'uploaded': _yt_date(v['snippet']['publishedAt'], lib.parent.cfg.get('urls', 'yt_date_format', '%b %d %Y')),
			'views': _yt_round(v['statistics']['viewCount']),
			'likes': _yt_round(v['statistics']['likeCount']),
			'dislikes': _yt_round(v['statistics']['dislikeCount']),
		})
	except urllib2.HTTPError as e:
		if e.getcode() == 403:
			return 'API limit exceeded'
		else:
			return str(e)
	except IndexError:
		return 'no results'
	except Exception as e:
		return str(e)

def gottwitch(uri):
	url = 'https://api.twitch.tv/helix/streams?user_login=%s' % uri.split('/')[0]
	opener = urllib2.build_opener()
	opener.addheaders = [('Client-ID', lib.parent.cfg.get('urls', 'twitch_api_key'))]
	respdata = opener.open(url).read()
	twitch = json.loads(respdata)['data']
	try:
		# TODO: add current game.
		return unescape('\037%s\037 is %s (%s)' % (twitch[0]['user_name'], twitch[0]['type'], twitch[0]['title']))
	except:
		return 'Channel offline.'

def goturl(url):
	for _, group, _ in other_regexes:
		for regex in group:
			if regex.match(url):
				return None
	request = urllib2.Request(url)
	opener = urllib2.build_opener(SmartRedirectHandler())
	try:
		soup = BeautifulSoup(opener.open(request, timeout=0.5))
		if soup.title:
			return unescape('%s' % (soup.title.string))
		else:
			return None
	except urllib2.HTTPError as e:
		return 'Error: %s %s' % (e.code, e.reason)
	except Exception as e:
		return 'Error: %r' % (e.message)

url_regex = (
	re.compile(r'https?://[^/\s]+\.[^/\s]+(?:/\S+)?'),
)
spotify_regex = (
	re.compile(r'spotify:(?P<type>\w+):(?P<track_id>\w{22})'),
	re.compile(r'https?://open.spotify.com/(?P<type>\w+)/(?P<track_id>\w+)')
)
youtube_regex = (
	re.compile(r'https?://(?:www\.)?youtube\.com/watch\?[a-zA-Z0-9=&_\-]+'),
)
twitch_regex = (
	re.compile(r'https?:\/\/(?:www\.)?twitch.tv\/([A-Za-z0-9]*)'),
)
other_regexes = (
	(gotspotify, spotify_regex, 'Spotify'),
	(gotyoutube, youtube_regex, 'YouTube'),
	(gottwitch, twitch_regex, 'Twitch'),
)
regexes = other_regexes + (
	(goturl, url_regex, 'Title'),
)
