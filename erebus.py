#!/usr/bin/python

#TODO: tons

import sys, select
import bot

class Erebus(object):
	pass

main = Erebus()
bots = {}
fds = {}
po = select.poll()

def setup():
	global bots, fds
	bots = {'erebus': bot.Bot(main, 'Erebus', 'erebus', '', 'irc.quakenet.org', 6667, 'Erebus', [])}
	fds = {}

	bots['erebus'].connect()
	fds[bots['erebus'].conn.fileno()] = bots['erebus']
	po.register(bots['erebus'].conn.fileno(), select.POLLIN)

def loop():
	poready = po.poll(60000)
	for (fd,mask) in poready:
		fds[fd].getdata()

if __name__ == '__main__':
	setup()
	while True:
		loop()
