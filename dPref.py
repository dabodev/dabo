import os
import datetime
import dabo
from dabo.dLocalize import _
import dabo.lib.utils as utils
try:
	from pysqlite2 import dbapi2 as sqlite
except ImportError:
	dabo.errorLog.write("This class requires SQLite")

# We don't want to deal with these as preferences.
regularAtts = ("_cache", "_parent", "_key", "_cursor", "_cxn", "_typeDict", "AutoPersist",
		"_autoPersist", "__methods__", "__basicsize__", "__members__", "_getAttributeNames", 
		"__itemsize__", "__base__", "__flags__", "__subclasses__", "__cmp__", "__bases__", 
		"__dictoffset__", "__call__", "__name__", "__mro__", "__weakrefoffset__", "mro")



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
	def __init__(self, key=None, crs=None, cxn=None):
		if key is None:
			self._key = ""
		else:
			self._key = key
		self._cache = {}
		self._autoPersist = True
		super(dPref, self).__init__()
		self._parent = None
		self._typeDict = {int: "int", float: "float", long: "long", str: "str", unicode: "unicode",
				bool: "bool", list: "list", tuple: "tuple", datetime.date: "date", 
				datetime.datetime: "datetime"}
		if crs is None:
			prefdir = utils.getUserDaboDirectory()
			self._cxn = dabo.db.dConnection(connectInfo={"dbType": "SQLite",
					"database": os.path.join(prefdir, "DaboPreferences.db")})
			self._cursor = self._cxn.getDaboCursor()
			# Make sure that the table exists
			if not  "daboprefs" in self._cursor.getTables():
				self._cursor.execute("create table daboprefs (ckey text not null, ctype text not null, cvalue text not null)")
		else:
			self._cursor = crs
			self._cxn = cxn
		
		
	def __getattr__(self, att):
		if att in regularAtts:
			if self.__dict__.has_key(att):
				return self.__dict__[att]
			else:
				return None
		if self.__dict__.has_key(att):
			ret = self.__dict__[att]
		elif self._cache.has_key(att):
			ret = self._cache[att]
		else:
			# See if it's in the database
			key = "%s.%s" % (self._getKey(), att)
			crs = self._cursor
			try:
				crs.execute("select ctype, cvalue from daboprefs where ckey = ? ", (key, ))
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
		if typ in ("str", "unicode"):
			ret = val
		elif typ == "date":
			ret = str((val.year, val.month, val.day))
		elif typ == "datetime":
			ret = str((val.year, val.month, val.day, val.hour, val.minute, val.second, val.microsecond))
		else:
			ret = unicode(val)
		return ret
		
	
	def _decodeType(self, rec):
		"""Take a record containing a cvalue and ctype, and convert the type
		as needed.
		"""
		val = rec["cvalue"]
		typ = rec["ctype"]
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
		elif typ in ("list", "tuple"):
			ret = eval(val)
		elif typ == "date":
			ret = eval("datetime.date%s" % val)
		elif typ == "datetime":
			ret = eval("datetime.datetime%s" % val)
		return ret

		
	def _persist(self, att, val):
		"""Writes the value of the particular att to the database with the proper key."""
		# Make sure that we have a valid key
		baseKey = self._getKey()
		if not baseKey:
			dabo.errorLog.write(_("No base key set; preference will not be persisted."))
			return
		key = "%s.%s" % (baseKey, att)
		crs = self._cursor
		try:
			typ = self._typeDict[type(val)]
		except:
			print "BAD TYPE", type(val)
			typ = "?"
		# Convert it to a string that can be properly converted back
		val = self._encodeType(val, typ)
		try:
			crs.execute("select ckey from daboprefs where ckey = ? ", (key, ))
			res = crs.RowCount
		except StandardError, e:
			print "UPD ERR", e
			res = -1
		if res > 0:
			sql = "update daboprefs set ctype = ?, cvalue = ? where ckey = ? "
			prm = (typ, val, key)
		else:
			sql = "insert into daboprefs (ckey, ctype, cvalue) values (?, ?, ?)"
			prm = (key, typ, val)
		crs.execute(sql, prm)
		crs.flush()
	
	
	def persist(self):
		"""Manually save preferences to the database."""
		for key, val in self._cache.items():
			if isinstance(val, dPref):
				# Child pref; tell it to persist itself
				val.persist()
			else:
				self._persist(key, val)
	
	
	def deletePref(self, att):
		"""Deletes a particular preference from both the database and the cache."""
		key = "%s.%s" % (self._getKey(), att)
		crs = self._cursor
		crs.execute("delete from daboprefs where ckey = ? ", (key, ))
		if self._cache.has_key(att):
			del self._cache[att]
	
	
	def deleteAllPrefs(self):
		"""Deletes all preferences for this object, and all sub-prefs as well."""
		key = "%s.%%" % self._getKey()
		crs = self._cursor
		crs.execute("delete from daboprefs where ckey like ? ", (key, ))
		for key, val in self._cache.items():
			if isinstance(val, dPref):
				# In case there are any other references to it hanging around,
				# clear its cache.
				val.flushCache()
		self._cache = {}		
	
	
	def flushCache(self):
		"""Clear the cache, forcing fresh reads from the database."""
		for key, val in self._cache.items():
			if isinstance(val, dPref):
				val.flushCache()
			else:
				del self._cache[key]
	
	
	def getPrefs(self, returnNested=False):
		"""Returns all the preferences set for this object. If returnNested is True,
		returns any sub-preferences too.
		"""
		crs = self._cursor
		key = self._getKey()
		sql = "select * from daboprefs where ckey like ?"
		crs.execute(sql, ("%s.%%" % key, ))
		ds = crs.getDataSet()
		if not returnNested:
			# Filter out all the results that are not first-level prefs
			keylen = len(key)+1
			ds = [rec for rec in ds
					if len(rec["ckey"][keylen:].split(".")) == 1]
		ret = {}
		for rec in ds:
			ret[rec["ckey"]] = self._decodeType(rec)
		return ret
	
	
	def getPrefKeys(self):
		"""Return a list of all preference keys for this key."""
		crs = self._cursor
		key = self._getKey()
		keylen = len(key) + 1
		keydots = len(key.split("."))
		sql = "select ckey from daboprefs where ckey like ?"
		crs.execute(sql, ("%s.%%" % key, ))
		rs = crs.getDataSet()
		ret = [rec["ckey"][keylen:] for rec in rs
				if len(rec["ckey"].split(".")) == keydots+1]
		# Now add any cached entries
		addl = [kk for kk in self._cache.keys()
			if kk not in ret and not isinstance(kk, dPref)]
		ret += addl
		return ret


	def getSubPrefKeys(self):
		"""Return a list of all 'child' keys for this key."""
		crs = self._cursor
		key = self._getKey()
		keylen = len(key) + 1
		keydots = len(key.split("."))
		sql = "select ckey from daboprefs where ckey like ?"
		crs.execute(sql, ("%s.%%" % key, ))
		rs = crs.getDataSet()
		retList = [rec["ckey"].split(".")[1] for rec in rs
				if len(rec["ckey"].split(".")) > 2]
		tmp = {}
		for itm in retList:
			tmp[itm] = None
		ret = tmp.keys()
		return ret

	
	# Property definitions start here
	def _getAutoPersist(self):
		ret = self._autoPersist
		if ret and self._parent is not None:
			# Make sure all parents are also auto-persist
			ret = ret and self._parent.AutoPersist
		return ret

	def _setAutoPersist(self, val):
		self._autoPersist = val


	AutoPersist = property(_getAutoPersist, _setAutoPersist, None,
			_("Do property assignments automatically save themselves? Default=True  (bool)"))
	
			
		

if __name__ == "__main__":
	a = dPref(key="TESTING")
	a.testValue = "First Level"
	a.anotherValue = "Another First"
	a.b.testValue = "Second Level"
	a.b.anotherValue = "Another Second"
	
	print "Just 'a' prefs:"
	print a.getPrefs()
	print
	print "'a' prefs and all sub-prefs:"
	print a.getPrefs(True)


	zz=a.getSubPrefKeys()
	print "SUB PREFS", zz
	
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
	
