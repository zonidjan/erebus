# Erebus IRC bot - Author: Erebus Team
# trivia module
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
def modstart(parent_arg, *args, **kwargs):
	global parent
	parent = parent_arg
	gotParent()
	return lib.modstart(parent, *args, **kwargs)
def modstop(*args, **kwargs):
	closeshop()
	return lib.modstop(*args, **kwargs)

# module code
import json

#setup
def gotParent():
	global jsonfile, db
	jsonfile = parent.cfg.get('userinfo', 'jsonpath', default="./modules/userinfo.json")
	db = json.load(open(jsonfile, "r"))
def closeshop():
	if json is not None and json.dump is not None:
		json.dump(db, open(jsonfile, "w"))#, indent=4, separators=(',', ': '))

#functions
def getauth(thing):
	if isinstance(thing, parent.User):
		if thing.auth is not None:
			return "#"+thing.auth
	elif isinstance(thing, basestring):
		if thing[0] == "#":
			return thing
		else:
			if parent.user(thing).auth is not None:
				return "#"+parent.user(thing).auth
	return None

def has(user, key):
	return (
		key in db.get(getauth(user), {}) or
		key in db.get(str(user).lower(), {})
	)
def get(user, key, default=None):
	return (
		db.get(getauth(user), {}).get(key,
		db.get(str(user).lower(), {}).get(key,
		default
	)))
def set(user, key, value):
	if getauth(user) is not None: db.setdefault(getauth(user), {})[key] = value
	db.setdefault(str(user).lower(), {})[key] = value

#commands
@lib.hook('get', needchan=False)
def cmd_get(bot, user, chan, realtarget, *args):
	if realtarget == chan.name: replyto = chan
	else: replyto = user

	if len(args) > 1:
		target = args[0]
		item = args[1]
	else:
		target = user
		item = args[0]

	value = get(target, item, None)
	if value is None:
		bot.msg(replyto, "%(user)s: %(item)s on %(target)s is not set." % {'user':user,'item':item,'target':target})
	else:
		bot.msg(replyto, "%(user)s: %(item)s on %(target)s: %(value)s" % {'user':user,'item':item,'target':target,'value':value})

@lib.hook('set', needchan=False)
@lib.argsGE(2)
def cmd_set(bot, user, chan, realtarget, *args):
	set(user, args[0], ' '.join(args[1:]))
	bot.msg(user, "Done.")

@lib.hook('oset', glevel=lib.STAFF, needchan=False)
@lib.argsGE(3)
def cmd_oset(bot, user, chan, realtarget, *args):
	set(args[0], args[1], ' '.join(args[2:]))
	bot.msg(user, "Done.")
