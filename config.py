# Erebus IRC bot - Author: John Runyon
# "Config" class (reading/providing access to bot.config)

import ConfigParser

class Config(object):
	def __init__(self, filename, writeout=True):
		self.__dict__['config'] = ConfigParser.SafeConfigParser()
		self.__dict__['filename'] = filename
		self.__dict__['writeout'] = writeout
		self.config.read(filename)

	def __getattr__(self, key):
		return self.config.get('erebus', key)

	def __setattr__(self, key, value):
		self.config.set('erebus', key, value)

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

	def set(self, section, key, value):
		self.config.set(section, key, value)

	def write(self):
		with open(self.filename, 'wb') as configfile:
			self.config.write(configfile)

	def __del__(self):
		if self.writeout: self.write()


if __name__ == '__main__':
	import sys
	cfg = Config(sys.argv[1], False)

	for k, v in cfg.items():
		print k, '=', v
