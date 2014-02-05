# Erebus IRC bot - Author: Conny Sjoblom
# Youtube URL Checker
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
import json
import urllib2
import urlparse
import HTMLParser
from BeautifulSoup import BeautifulSoup

checkfor = "youtube"
url_regex = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
yturl_regex = re.compile('(http|ftp|https):\/\/([\w\-_]+(?:(?:\.[\w\-_]+)+))([\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?')

@lib.hooknum("PRIVMSG")
def privmsg_hook(bot, line):
	try:
		linetx = line.split(None, 3)[3][1:]
	except IndexError:
		linetx = ''

	if checkfor not in line:
		return # doesn't concern us

	print "Meow"
	for url in url_regex.findall(linetx):
		if checkfor in url:
			url_data = urlparse.urlparse(url)
			query = urlparse.parse_qs(url_data.query)
			video = query["v"][0]
			api_url = 'http://gdata.youtube.com/feeds/api/videos/%s?alt=json&v=2' % video
			respdata = urllib2.urlopen(api_url).read()
			video_info = json.loads(respdata)

			title = video_info['entry']['title']["$t"]
			author = video_info['entry']['author'][0]['name']['$t']

			bot.msg(line.split()[2], "Youtube: %s (%s)" % (title, author))
