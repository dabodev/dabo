# -*- coding: utf-8 -*-
import os
import warnings
import datetime
from decimal import Decimal
import dabo
from dabo.dLocalize import _
import dabo.lib.utils as utils
from dabo.lib.utils import ustr
import dabo.db


# We don't want to deal with these as preferences.
regularAtts = ("AutoPersist", "__base__", "__bases__", "__basicsize__", "__call__",
		"__cmp__", "_deletionCache", "__dictoffset__", "__flags__", "__itemsize__",
		"__members__", "__methods__", "__mro__", "__name__", "__subclasses__",
		"__weakrefoffset__", "_autoPersist", "_cache", "_cursor", "_cxn", "get",
		"_getAttributeNames", "_key", "_noneType", "_parent", "_persistAll", "_typeDict", "mro")


class dPref(object):
	"""dPref is a class that is used to automatically manage preferences. It requires
	SQLite in order to function; without that installed, you cannot use this class. It
	automatically supports nesting of preferences; if you have a dPref object named
	'basePref', and then issue the statement 'basePref.subPref.something=True', a
	new dPref object named 'subPref' will be created, and can be referred to using
	'basePref.subPref'.

	Normally you should specify the initial key for your prefs. This will ensure that
	your preference names do not conflict with other dabo preferences. This is much like
	the approach to modules in the Python namespace. Failure to specify a base
	key would put all of your prefs into the 'root' namespace, where collisions can more
	easily happen, and thus is not allowed.

	All preference assignments are automatically persisted to the database unless
	the 'AutoPersist' property on this object or one of its 'ancestors' is set to False.
	When that is False, you must call the persist() method manually, or your settings
	will not be saved. Calling 'persist()' will write any values of that object and all of its
	child objects to the database.
	"""
	def __init__(self, key=None, crs=None, cxn=None, appName="Dabo", prefDb=None):
		if key is None:
			self._key = ""
		else:
			self._key = key
		self._cache = {}
		self._deletionCache = {}
		self._autoPersist = True
		# Do we save even without a base key? This should only
		# be changed by framework tools designed to access the
		# the preference database.
		self._persistAll = False
		super(dPref, self).__init__()
		self._parent = None
		self._noneType = type(None)
		self._typeDict = {int: "int", float: "float", long: "long", str: "str", unicode: "unicode",
				bool: "bool", list: "list", tuple: "tuple", datetime.date: "date", dict: "dict",
				datetime.datetime: "datetime", Decimal: "decimal", self._noneType: "none",
				dabo.db.dDataSet: "tuple"}
		if crs is None:
			if prefDb:
				db = prefDb
			else:
				prefdir = utils.getUserAppDataDirectory(appName)
				if prefdir is None:
					# pkm: This happened to me on a webserver where the user is www-data who doesn't have
					#      a home directory. I actually don't care about preferences in this case but I
					#      wasn't able to set dApp.PreferenceManager to None unfortunately, so we'll just
					#      punt and put the preference db in the working directory (up to your webapp to
					#      chdir() accordingly)..
					prefdir = os.getcwd()
				db = os.path.join(prefdir, "DaboPreferences.db")
			if cxn:
				self._cxn = cxn
			else:
				self._cxn = dabo.db.dConnection(connectInfo={"DbType": "SQLite", "Database": db},
						forceCreate=True)
			self._cursor = self._cxn.getDaboCursor()
			self._cursor.IsPrefCursor = True
			# Make sure that the table exists
			if not  "daboprefs" in self._cursor.getTables():
				self._cursor.execute("create table daboprefs (ckey text not null, ctype text not null, cvalue text not null)")
				self._cursor.commitTransaction()
		else:
			self._cursor = crs
			self._cxn = cxn


	def __getattr__(self, att):
		if att in regularAtts:
			try:
				return self.__dict__[att]
			except KeyError:
				return None
		try:
			ret = self.__dict__[att]
		except KeyError:
			try:
				ret = self._cache[att]
			except KeyError:
				# See if it's in the database
				key = self._getKey()
				if key:
					param = "%s.%s" % (key, att)
				else:
					param = att
				crs = self._cursor
				try:
					crs.execute("select ctype, cvalue from daboprefs where ckey = ? ", (param, ))
					rec = crs.getCurrentRecord()
				except StandardError, e:
					print "QUERY ERR", e
					rec = {}
				if rec:
					ret = self._decodeType(rec)
				else:
					ret = dPref(crs=self._cursor, cxn = self._cxn)
					ret._parent = self
					ret._key = att
				self._cache[att] = ret
		return ret


	def __setattr__(self, att, val):
		if att in regularAtts:
			super(dPref, self).__setattr__(att, val)
			#self.__dict__[att] = val
			return
		persist = False
		try:
			curr = self._cache[att]
			exists = True
		except KeyError:
			exists = False
			persist = self.AutoPersist
		if exists:
			persist = (curr != val) and self.AutoPersist
		if persist:
			self._persist(att, val)
		self._cache[att] = val


	def get(self, att):
		"""If the specified name is a subkey, it is returned. If it is a value, the value is
		returned. If it doesn't exist, a new subkey is created with that name.
		"""
		return self.__getattr__(att)


	def _getKey(self):
		"""The key is a concatenation of this object's name and the names of its
		ancestors, separated with periods.
		"""
		ret = self._key
		if not ret:
			ret = ""
		else:
			if self._parent is not None:
				ret = ".".join((self._parent._getKey(), ret))
		return ret


	def _encodeType(self, val, typ):
		"""Takes various value types and converts them to a string formats that
		can be converted back when needed.
		"""
		if typ == "date":
			ret = ustr((val.year, val.month, val.day))
		elif typ == "datetime":
			ret = ustr((val.year, val.month, val.day, val.hour, val.minute, val.second, val.microsecond))
		else:
			ret = ustr(val)
		return ret


	def _decodeType(self, rec):
		"""Take a record containing a cvalue and ctype, and convert the type
		as needed.
		"""
		val = rec["cvalue"]
		typ = rec["ctype"]
		ret = None
		if typ in ("str", "unicode"):
			ret = val
		elif typ == "int":
			ret = int(val)
		elif typ == "float":
			ret = float(val)
		elif typ == "long":
			ret = long(val)
		elif typ == "bool":
			ret = (val == "True")
		elif typ in ("list", "tuple", "dict"):
			ret = eval(val)
		elif typ == "date":
			ret = eval("datetime.date%s" % val)
		elif typ == "datetime":
			ret = eval("datetime.datetime%s" % val)
		elif typ == "decimal":
			ret = Decimal(val)
		elif typ == "none":
			ret = None
# 		if ret is None:
# 			print "NONE", rec
		return ret


	def _persist(self, att, val):
		"""Writes the value of the particular att to the database with the proper key."""
		# Make sure that we have a valid key
		baseKey = self._getKey()
		if not baseKey:
			if not self._persistAll:
				dabo.log.error(_("No base key set; preference will not be persisted."))
				return
			else:
				key = att
		else:
			key = "%s.%s" % (baseKey, att)
		crs = self._cursor
		try:
			typ = self._typeDict[type(val)]
		except KeyError:
			dabo.log.error(_("BAD TYPE: %s") % type(val))
			typ = "?"
		# Convert it to a string that can be properly converted back
		val = self._encodeType(val, typ)

		sql = "update daboprefs set ctype = ?, cvalue = ? where ckey = ? "
		prm = (typ, val, key)
		crs.execute(sql, prm)
		# Use the dbapi-level 'rowcount' attribute to get the number
		# of affected rows.
		if not crs.rowcount:
			sql = "insert into daboprefs (ckey, ctype, cvalue) values (?, ?, ?)"
			prm = (key, typ, val)
			crs.execute(sql, prm)
		self._cursor.commitTransaction()


	def persist(self):
		"""Manually save preferences to the database."""
		for key, val in self._cache.items():
			if isinstance(val, dPref):
				# Child pref; tell it to persist itself
				val.persist()
			else:
				self._persist(key, val)
		# Handle the cached deletions
		for key in self._deletionCache:
			self._cursor.execute("delete from daboprefs where ckey like ? ", (key, ))
		self._deletionCache = {}
		self._cursor.commitTransaction()


	def deletePref(self, att, nested=False):
		"""Deletes a particular preference from both the database
		and the cache. If 'nested' is True, and the att is a node containing
		sub-prefs, that node and all its children will be deleted.
		"""
		basekey = self._getKey()
		if basekey:
			key = "%s.%s" % (basekey, att)
		else:
			key = att
		crs = self._cursor
		if nested:
			key += "%"
		if self._autoPersist:
			if nested:
				crs.execute("delete from daboprefs where ckey like ? ", (key, ))
			else:
				crs.execute("delete from daboprefs where ckey = ? ", (key, ))
		else:
			self._deletionCache[key] = None
		try:
			del self._cache[att]
		except KeyError:
			pass
		self._cursor.commitTransaction()


	def deleteAllPrefs(self):
		"""Deletes all preferences for this object, and all sub-prefs as well."""
		basekey = self._getKey()
		if not basekey:
			return
		key = "%s.%%" % basekey
		if self._autoPersist:
			crs = self._cursor
			crs.execute("delete from daboprefs where ckey like ? ", (key, ))
			for key, val in self._cache.items():
				if isinstance(val, dPref):
					# In case there are any other references to it hanging around,
					# clear its cache.
					val.flushCache()
			self._cache = {}
		else:
			# Update the caches
			self._cache = {}
			self._deletionCache[key] = None
		self._cursor.commitTransaction()


	def deleteByValue(self, val):
		"""Removes any preferences at or below this object whose value
		matches the passed value.
		"""
		crs = self._cursor
		sql = """delete from daboprefs
				where ckey like ?
				and cvalue = ?"""
		prm = ("%s%%" % self._getKey(), val)
		crs.execute(sql, prm)
		crs.commitTransaction()


	def flushCache(self):
		"""Clear the cache, forcing fresh reads from the database."""
		for key, val in self._cache.items():
			if isinstance(val, dPref):
				val.flushCache()
			else:
				del self._cache[key]
	cancel = flushCache


	def getPrefs(self, returnNested=False, key=None, asDataSet=False):
		"""Returns all the preferences set for this object. If returnNested is True,
		returns any sub-preferences too.
		"""
		crs = self._cursor
		if key is None:
			key = self._getKey()
		elif key.startswith("."):
			# It's relative to this key
			key = ".".join((self._getKey(), key[1:]))
		key = key.replace("_", r"\_")
		param = "%(key)s%%" % locals()
		sql = "select * from daboprefs where ckey like ? escape '\\' "
		crs.execute(sql, (param, ))
		ds = crs.getDataSet()
		if not returnNested:
			# Filter out all the results that are not first-level prefs
			keylen = len(key)+1
			ds = [rec for rec in ds
					if len(rec["ckey"][keylen:].split(".")) == 1]
		if asDataSet:
			return ds
		ret = {}
		for rec in ds:
			ret[rec["ckey"]] = self._decodeType(rec)
		return ret


	def getPrefKeys(self, spec=None):
		"""Return a list of all preference keys for this key."""
		crs = self._cursor
		key = self._getKey()
		if spec is not None:
			key = ".".join((key, spec))
		keylen = len(key) + 1
		keydots = len(key.split("."))
		sql = "select ckey from daboprefs where ckey like ?"
		crs.execute(sql, ("%s.%%" % key, ))
		rs = crs.getDataSet()
		tmpDict = {}
		for rec in rs:
			tmpDict[rec["ckey"][keylen:keylen+len(rec["ckey"].split(".")[keydots])]] = None
		# Now add any cached entries
		ret = list(set(tmpDict) | set([kk for kk in self._cache
			if kk.startswith(key) and not isinstance(kk, dPref)]))
		return ret


	def hasKey(self, key):
		"""Provides a way to test for a key without automatically adding it."""
		return key in self.getPrefKeys()
	__contains__ = hasKey


	def getSubPrefKeys(self, spec=None):
		"""Return a list of all 'child' keys for this key."""
		crs = self._cursor
		key = self._getKey()
		if spec is not None:
			key = ".".join((key, spec))
		keydots = len(key.split("."))
		sql = "select ckey from daboprefs where ckey like ?"
		crs.execute(sql, ("%s.%%" % key, ))
		rs = crs.getDataSet()
		retList = [rec["ckey"].split(".")[keydots] for rec in rs
				if len(rec["ckey"].split(".")) > 2]
		tmp = {}
		for itm in retList:
			tmp[itm] = None
		return tmp.keys()


	def getValue(self, key):
		"""Given a key, returns the corresponding value, or a
		dPref object if it exists as a sub key. If there is no match
		for 'key', None is returned.
		"""
		ret = self.__getattr__(key)
		if isinstance(ret, dPref):
			ret = None
		return ret


	def addKey(self, key, typ, val):
		"""Adds a new key to the base key."""
		newTyp = self._typeDict[typ]
		sql = "insert into daboprefs (ckey, ctype, cvalue) values (?, ?, ?)"
		prm = (key, newTyp, val)
		self._cursor.execute(sql, prm)
		self._cursor.commitTransaction()


	def setValue(self, key, val):
		"""Given a key and value, sets the preference to that value."""
		self.__setattr__(key, val)


	def getPrefTree(self, spec=None):
		"""Returns a tree-like series of nested preference keys."""
		crs = self._cursor
		key = self._getKey()
		if spec is not None:
			key = ".".join((key, spec))
		sql = "select ckey from daboprefs where ckey like ? order by ckey"
		if key:
			param = "%s.%%" % key
		else:
			param = "%"
		crs.execute(sql, (param,))
		rs = crs.getDataSet()
		vs = [itm.values()[0] for itm in rs]

		def uniqKeys(dct, val):
			dct[val] = None

		def mkTree(vals):
			ret = []
			# Get all the first-tier keys
			# get all the first level values
			lev0 = [val.split(".", 1)  for val in vals]
			keys = {}
			[uniqKeys(keys, itm[0]) for itm in lev0]
			for key in sorted(keys):
				keylist = [key]
				try:
					kids = [itm[1] for itm in lev0
							if itm[0] == key]
				except IndexError:
					kids = None
				if kids:
					keylist.append(mkTree(kids))
				ret.append(keylist)
			return ret

		return mkTree(vs)


	def __nonzero__(self):
		"""Preference instances should always evaluate to a boolean False,
		as they represent a lack of a value; i.e., a dot-separated path, but
		not an actual stored value."""
		return False


	# Property definitions start here
	def _getAutoPersist(self):
		ret = self._autoPersist
		if ret and self._parent is not None:
			# Make sure all parents are also auto-persist
			ret = ret and self._parent.AutoPersist
		return ret

	def _setAutoPersist(self, val):
		self._autoPersist = val


	def _getFullPath(self):
		return self._getKey()


	AutoPersist = property(_getAutoPersist, _setAutoPersist, None,
			_("Do property assignments automatically save themselves? Default=True  (bool)"))

	FullPath = property(_getFullPath, None, None,
			_("""The fully-qualified path to this object, consisting of all ancestor
			names along with this name, joined by periods (read-only) (str)"""))






if __name__ == "__main__":
	a = dPref(key="TESTING")
	a.testValue = "First Level"
	a.anotherValue = "Another First"
	a.b.testValue = "Second Level"
	a.b.anotherValue = "Another Second"
	a.b.c.CrazyMan = "Ed"

	print a.getPrefKeys()
	print a.b.getPrefKeys()
	print a.b.c.getPrefKeys()

	a.deletePref("b.c")
	print a.getPrefs(True)
	a.deletePref("b.c", True)
	print a.getPrefs(True)

	print "Just 'a' prefs:"
	print a.getPrefs()
	print
	print "'a' prefs and all sub-prefs:"
	print a.getPrefs(True)

	zz=a.getSubPrefKeys()
	print "SUB PREFS", zz
	zz = a.getPrefKeys()
	print "PREF KEYS", zz

	a.AutoPersist = False
	a.b.shouldntStay = "XXXXXXXXXX"

	print "BEFORE FLUSH", a.b.getPrefKeys()
	a.flushCache()
	print "AFTER FLUSH", a.b.getPrefKeys()

	print "DELETE ONE"
	a.deletePref("anotherValue")
	print a.getPrefs(True)
	print "DELETE ALL"
	a.deleteAllPrefs()
	print a.getPrefs(True)
