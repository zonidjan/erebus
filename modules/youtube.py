# Erebus IRC bot - Author: Erebus Team
# Youtube URL Checker
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
import json
import urllib2
import urlparse
import HTMLParser
from BeautifulSoup import BeautifulSoup

checkfor = "youtube"
yturl_regex = re.compile(r'https?://(?:www\.)?youtube\.com/watch\?[a-zA-Z0-9=&]+')

@lib.hooknum("PRIVMSG")
def privmsg_hook(bot, line):
	try:
		linetx = line.split(None, 3)[3][1:]
	except IndexError:
		linetx = ''

	if checkfor not in line:
		return # doesn't concern us

	for url in yturl_regex.findall(linetx):
		url_data = urlparse.urlparse(url)
		query = urlparse.parse_qs(url_data.query)
		video = query["v"][0]
		api_url = 'http://gdata.youtube.com/feeds/api/videos/%s?alt=json&v=2' % video
		try:
			respdata = urllib2.urlopen(api_url).read()
			video_info = json.loads(respdata)

			title = video_info['entry']['title']["$t"]
			author = video_info['entry']['author'][0]['name']['$t']

			bot.msg(line.split()[2], "Youtube: %s (%s)" % (title, author))
		except:
			pass
