# Erebus IRC bot - Author: Erebus Team
# userinfo module
# This file is released into the public domain; see http://unlicense.org/

# module info
modinfo = {
	'author': 'Erebus Team',
	'license': 'public domain',
	'compatible': [0],
	'depends': [],
	'softdeps': ['help'],
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
	savedb()
	return lib.modstop(*args, **kwargs)

# module code
import json

#setup
def gotParent():
	global jsonfile, db
	jsonfile = parent.cfg.get('userinfo', 'jsonpath', default="./modules/userinfo.json")
	try:
		db = json.load(open(jsonfile, "r"))
	except:
		db = {}
def savedb():
	if json is not None and json.dump is not None and db != {}:
		json.dump(db, open(jsonfile, "w"))#, indent=4, separators=(',', ': '))

#functions
def _getauth(thing):
	if isinstance(thing, parent.User):
		if thing.auth is not None:
			return "#"+thing.auth
	elif isinstance(thing, basestring):
		if thing.startswith("#"):
			return thing
		else:
			if parent.user(thing).auth is not None:
				return "#"+parent.user(thing).auth
	return None

def _keys(user):
	return list(set(db.get(_getauth(user), {}).keys() + db.get(str(user).lower(), {}).keys())) #list-to-set-to-list to remove duplicates
def _has(user, key):
	key = key.lower()
	return (
		key in db.get(_getauth(user), {}) or
		key in db.get(str(user).lower(), {})
	)
def _get(user, key, default=None):
	key = key.lower()
	return (
		db.get(_getauth(user), {}). #try to get the auth
			get(key, #try to get the info-key by auth
			db.get(str(user).lower(), {}). #fallback to using the nick
				get(key, #and try to get the info-key from that
				default #otherwise throw out whatever default
	)))
def _set(user, key, value):
	key = key.lower()
	if _getauth(user) is not None:
		db.setdefault(_getauth(user), {})[key] = value #use auth if we can
	db.setdefault(str(user).lower(), {})[key] = value #but set nick too
def _del(user, key):
	key = key.lower()
	auth = _getauth(user)
	if auth is not None and auth in db and key in db[auth]:
		del db[auth][key]
	target = str(user).lower()
	if target in db and key in db[target]:
		del db[target][key]

#commands
@lib.hook(needchan=False, wantchan=True)
@lib.help("[<target>]", "lists info items known about someone", "<target> may be a nick, or an auth in format '#auth'", "it defaults to yourself")
def getitems(bot, user, chan, realtarget, *args):
	if chan is not None: replyto = chan
	else: replyto = user

	if len(args) > 0:
		target = args[0]
	else:
		target = user

	bot.msg(replyto, "%(user)s: %(target)s has the following info items: %(items)s" % {'user':user,'target':target,'items':(', '.join(_keys(target)))})

@lib.hook(needchan=False, wantchan=True)
@lib.help("[<target>] <item>", "gets an info item about someone", "<target> may be a nick, or an auth in format '#auth'", "it defaults to yourself")
@lib.argsGE(1)
def getinfo(bot, user, chan, realtarget, *args):
	if chan is not None: replyto = chan
	else: replyto = user

	if len(args) > 1:
		target = args[0]
		item = args[1]
	else:
		target = user
		item = args[0]

	value = _get(target, item, None)
	if value is None:
		bot.msg(replyto, "%(user)s: %(item)s on %(target)s is not set." % {'user':user,'item':item,'target':target})
	else:
		bot.msg(replyto, "%(user)s: %(item)s on %(target)s: %(value)s" % {'user':user,'item':item,'target':target,'value':value})

@lib.hook(needchan=False)
@lib.help("<item> <value>", "sets an info item about you")
@lib.argsGE(2)
def setinfo(bot, user, chan, realtarget, *args):
	_set(user, args[0], ' '.join(args[1:]))
	savedb()
	bot.msg(user, "Done.")

@lib.hook(needchan=False)
@lib.help("<item>", "deletes an info item about you")
@lib.argsEQ(1)
def delinfo(bot, user, chan, realtarget, *args):
	_del(user, args[0])
	savedb()
	bot.msg(user, "Done.")

@lib.hook(glevel=lib.ADMIN, needchan=False)
@lib.help("<target> <item> <value>", "sets an info item about someone else", "<target> may be a nick, or an auth in format '#auth'")
@lib.argsGE(3)
def osetinfo(bot, user, chan, realtarget, *args):
	_set(args[0], args[1], ' '.join(args[2:]))
	savedb()
	bot.msg(user, "Done.")

@lib.hook(glevel=lib.STAFF, needchan=False)
@lib.help("<target> <item>", "deletes an info item about someone else", "<target> may be a nick, or an auth in format '#auth'")
@lib.argsEQ(2)
def odelinfo(bot, user, chan, realtarget, *args):
	_del(args[0], args[1])
	savedb()
	bot.msg(user, "Done.")
