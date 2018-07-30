# Erebus IRC bot - Author: John Runyon
# vim: fileencoding=utf-8
# "Config" class (reading/providing access to bot.config)

from __future__ import print_function
import sys

if sys.version_info.major < 3:
	import ConfigParser
else:
	import configparser as ConfigParser

class Config(object):
	def __init__(self, filename, writeout=True):
		self.__dict__['config'] = ConfigParser.RawConfigParser()
		self.__dict__['filename'] = filename
		self.__dict__['writeout'] = writeout
		self.config.read(filename)

	def __getattr__(self, key):
		return self.config.get('erebus', key)

	def __setattr__(self, key, value):
		self.config.set('erebus', key, value)

	def __getitem__(self, section): #!! READ-ONLY !!
		return {item: self.config.get(section, item) for item in self.config.options(section)}

	def level(self, cmd):
		return self.config.get('levels', cmd)

	def setlevel(self, cmd, level):
		self.config.set('levels', cmd, level)

	def items(self, section='erebus'):
		return self.config.items(section)

	def get(self, section, key, default=None):
		try:
			return self.config.get(section, key)
		except:
			return default
	def getboolean(self, section, key):
		val = self.get(section, key, False)
		if val == False or val == "0" or val.lower() == "false":
			return False
		else:
			return True

	def set(self, section, key, value):
		self.config.set(section, key, value)
		if self.writeout: self.write()

	def write(self):
		with open(self.filename, 'wb') as configfile:
			self.config.write(configfile)

	def __del__(self):
		if self.writeout: self.write()

if __name__ == '__main__':
	import sys
	if len(sys.argv) > 1:
		cfg = Config(sys.argv[1], False)
	else:
		cfg = Config('bot.config', False)

	for s in cfg.config.sections():
		for k, v in cfg.items(s):
			print("[%r][%r] = %r" % (s, k, v))
