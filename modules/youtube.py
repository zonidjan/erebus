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
import urllib2
import HTMLParser
from BeautifulSoup import BeautifulSoup

checkfor = "youtube"
hostmask_regex = re.compile('^(.*)!(.*)@(.*)$')
url_regex = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
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

	for url in url_regex.findall(linetx):
		if checkfor in url:
			html_parser = HTMLParser.HTMLParser()
			respdata = urllib2.urlopen(url).read()
			soup = BeautifulSoup(respdata)
			bot.msg(line.split()[2], BeautifulSoup(soup.title.string, convertEntities=BeautifulSoup.HTML_ENTITIES))
