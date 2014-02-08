# Erebus IRC bot - Author: Erebus Team
# simple coin module
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
import requests

coin_regex = (
	re.compile(r'([0-9.,\s]+)\s(btc|bitcoin|doge|dogecoin|ltc|litecoin)'),
)

cur_regex = (
	re.compile(r'([0-9.,\s]+)\s([a-zA-Z]{3})\sin\s([a-zA-Z]{3})'),
)

url = 'http://www.cryptocoincharts.info/v2/api/tradingPairs'

def get_coin_price(pairs):
	response = requests.post(url, data = {'pairs': pairs})
	return json.loads(response.text)

@lib.hook('btc')
def cmd_gtest(bot, user, chan, realtarget, *args):
	if len(args) > 0:
		try:
			response = get_coin_price('btc_eur')
			price = str(float(response[0]['price']) * float(args[0]))
			bot.msg(chan, "%s BTC = %s EUR" % (args[0], price))
		except:
			bot.msg(chan, "Invalid amount.")
	else:
		response = get_coin_price('btc_eur')
		price = str(float(response[0]['price']))
		bot.msg(chan, "1 BTC = %s EUR" % price)

@lib.hook('doge')
def cmd_gtest(bot, user, chan, realtarget, *args):
	if len(args) > 0:
		try:
			doge_btc = get_coin_price('doge_btc')
			btc_eur = get_coin_price('btc_eur')
			price = str(float(doge_btc[0]['price']) * float(btc_eur[0]['price']) * float(args[0]))
			bot.msg(chan, "%s DOGE = %s EUR" % (args[0], price))
		except:
			bot.msg(chan, "Invalid amount.")
	else:
		doge_btc = get_coin_price('doge_btc')
		btc_eur = get_coin_price('btc_eur')
		price = str(float(doge_btc[0]['price']) * float(btc_eur[0]['price']))
		bot.msg(chan, "1 DOGE = %s EUR" % price)

@lib.hook('ltc')
def cmd_gtest(bot, user, chan, realtarget, *args):
	if len(args) > 0:
		try:
			ltc_btc = get_coin_price('ltc_btc')
			btc_eur = get_coin_price('btc_eur')
			price = str(float(ltc_btc[0]['price']) * float(btc_eur[0]['price']) * float(args[0]))
			bot.msg(chan, "%s LTC = %s EUR" % (args[0], price))
		except:
			bot.msg(chan, "Invalid amount.")
	else:
		ltc_btc = get_coin_price('ltc_btc')
		btc_eur = get_coin_price('btc_eur')
		price = str(float(ltc_btc[0]['price']) * float(btc_eur[0]['price']))
		bot.msg(chan, "1 LTC = %s EUR" % price)

@lib.hooknum("PRIVMSG")
def privmsg_hook(bot, line):

	try:
		linetx = line.split(None, 3)[3][1:]
	except IndexError:
		linetx = ''

	chan = line.split()[2]

	if 'in' in line:
		for r in cur_regex:
			for a, f, t in r.findall(linetx):

				# https://www.google.com/finance/converter?a=1.2&from=USD&to=EUR

				a = a.replace(",", ".")
				a = a.replace(" ", "")
				print a
				print f
				print t

	if 'btc' in line or 'bitcoin' in line or 'doge' in line or 'dogecoin' in line:
		for r in coin_regex:
			for amount, coin in r.findall(linetx):
				amount = amount.replace(",", ".")
				amount = amount.replace(" ", "")
				if 'btc' in coin or 'bitcoin' in coin:
					try:
						response = get_coin_price('btc_eur')
						price = str(float(response[0]['price']) * float(amount))
						bot.msg(chan, "%s BTC = %s EUR" % (amount, price))
					except:
						pass

				if 'ltc' in coin or 'litecoin' in coin:
					pass	# Add LTC

				if 'doge' in coin or 'dogecoin' in coin:
					try:
						doge_btc = get_coin_price('doge_btc')
						btc_eur = get_coin_price('btc_eur')
						price = str(float(doge_btc[0]['price']) * float(btc_eur[0]['price']) * float(amount))
						bot.msg(chan, "%s DOGE = %s EUR" % (amount, price))
					except:
						bot.msg(chan, "Invalid amount.")


				print amount
				print coin
