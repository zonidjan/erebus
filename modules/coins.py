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
import json
import requests

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
