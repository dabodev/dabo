# -*- coding: utf-8 -*-
import pickle
import os
import time

import dabo
from dabo.dLocalize import _
import dabo.dConstants as kons
from dabo.lib.connParser import importConnections
import dabo.dException as dException
from dBizobj import dBizobj



class RemoteBizobj(dBizobj):
	cacheDir = None

	def _beforeInit(self):
		return super(RemoteBizobj, self)._beforeInit()


	def _afterInit(self):
		# This is used as the identifier that connects to the client bizobj
		self.hashval = None
		self.defineConnection()
		super(RemoteBizobj, self)._afterInit()


	@classmethod
	def _createCacheDir(cls, pth=None):
		if cls.cacheDir is not None:
			return
		if pth is None:
			pth = os.getcwd()
		cls.cacheDir = os.path.join(pth, "cache")
		if not os.path.exists(cls.cacheDir):
			os.makedirs(cls.cacheDir)


	def defineConnection(self):
		"""You must define and create the connection in this method. Otherwise
		an error will be raised. Pass the connection information to setConnectionParams();
		if you are using a .cnxml file, pass that in the 'cxnfile' parameter; otherwise, use
		the various connection setting params to define the connection.
		NOTE: You must use a SINGLE-CONNECTION .cnxml file; if multiple connections
		are defined, there is no way for the bizobj to know which one you want to use.
		"""
		# Force an override in child bizobjs
		raise NotImplementedError


	@classmethod
	def load(cls, hashval, ds, pth):
		biz = cls()
		biz.DataSource = ds
		biz.hashval = hashval

		cls._createCacheDir(pth)
		pth = os.path.join(cls.cacheDir, hashval)
		if os.path.exists(pth):
			f = file(pth)
			kf, crsData = pickle.load(f)
			f.close()
			biz.KeyField = kf
			# This is a dict with cursor keys as the keys, and
			# values as a (dataset, typedef) tuple.
			for kk, (ds, typinfo) in crsData.items():
				tmpCursor = biz.createCursor(key=kk)
				tmpCursor._storeData(ds, typinfo)
		return biz


	def setConnectionParams(self, cxnfile=None, dbType=None, database=None,
			host=None, user=None, password=None, plainTextPassword=None):
		if cxnfile:
			cxDict = importConnections(cxnfile)
			self.setConnection(cxDict.values()[0])
		else:
			cxnDict = {"DbType": dbType, "Database": database}
			if host:
				cxnDict["Host"]  = host
			if user:
				cxnDict["User"] = user
			if plainTextPassword:
				cxnDict["PlainTextPassword"] = plainTextPassword
			if password:
				cxnDict["Password"] = password
			ci = dabo.db.dConnectInfo(cxnDict)
			cn = dabo.db.dConnection(ci)
			self.setConnection(cn)


	def storeToCache(self, hashval):
		"""Store data info to the cache for the next time the same bizobj
		is needed.
		"""
		self._createCacheDir()
		pth = os.path.join(self.cacheDir, hashval)
		f = file(pth, "w")
		pd = {}
		cursorDict = self._cursorDictReference()
		for kk, cursor in cursorDict.items():
			pd[kk] = (cursor.getDataSet(returnInternals=True), cursor.getDataTypes())
		dataToStore = (self.KeyField, pd)
		pickle.dump(dataToStore, f)
		f.close()


	def storeRemoteSQL(self, sql):
		"""The web backend uses '~~' as the name enclosure character. Convert that
		to the correct character for the actual backend.
		"""
		remoteChar = "~~"
		localChar = self._CurrentCursor.BackendObject.nameEnclosureChar
		self.UserSQL = sql.replace(remoteChar, localChar)


	def applyDiffAndSave(self, diff, primary=False):
		"""Diffs are dicts in the format:

			{hashval: (DataSource, KeyField, [changes])}

		where 'changes' is a list of dicts; one for each changed row in
		the bizobj. Each row dict has the following key/value pairs:

			KeyField: pk value
			ColumnName: (origVal, newVal)
			Column2Name: (origVal, newVal)
			...

		The 'diff' dict we receive can have 1 or two keys. One that will always
		be present is the hashval for this bizobj. If this bizobj has related child
		bizobjs, and they have changes, there will be a 'children' key that will
		contain a list of one diff for each child bizobj with changes.

		If this is the primary bizobj called from the web server, the 'primary'
		parameter will be true, meaning that this bizobj will handle transactions.
		"""
		if primary:
			self._CurrentCursor.beginTransaction()
		myDiff = diff.pop(self.hashval, None)
		if myDiff:
			self.DataSource = myDiff[0]
			self.KeyField = kf = myDiff[1]
			changeRecs = myDiff[2]
			kids = myDiff[3]
			for rec in changeRecs:
				newrec = rec.get(kons.CURSOR_TMPKEY_FIELD, False)
				if newrec:
					self.new()
				else:
					pk = rec.get(kf)
					try:
						self.moveToPK(pk)
					except dException.RowNotFoundException:
						ds = self.DataSource
						raise dException.WebServerException(
								_("PK '%(pk)s' not present in dataset for DataSource '%(ds)s'") % locals())
				for col, vals in rec.items():
					if col in (kf, kons.CURSOR_TMPKEY_FIELD):
						continue
					oldval, newval = vals
					if not newrec:
						# Check for update conflicts; abort if found
						currval = self.getFieldVal(col)
						if currval != oldval:
							raise dException.WebServerException(
									_("Update Conflict: the value in column '%s' has been changed by someone else.") % col)
					self.setFieldVal(col, newval)

			if kids:
				for kidHash, kidInfo in kids.items():
					kidDS, kidKey, kidData, kidKids = kidInfo
					kidClass = dabo._bizDict.get(kidDS)
					if not kidClass:
						abort(404, _("DataSource '%s' not found") % kidDS)
					kidBiz = kidClass.load(kidHash, kidDS)
					kidBiz.applyDiffAndSave({kidHash: kidInfo})

			try:
				self.saveAll()
			except dException.ConnectionLostException, e:
				if primary:
					self._CurrentCursor.rollbackTransaction()
					return (500, _("Connection to database was lost."))
				else:
					raise
			except dException.NoRecordsException, e:
				if primary:
					self._CurrentCursor.rollbackTransaction()
					return (204, _("No records were saved."))
				else:
					raise
			except dException.BusinessRuleViolation, e:
				if primary:
					self._CurrentCursor.rollbackTransaction()
					return (409, _("Business Rule Violation: %s.") % e)
				else:
					raise
			except dException.DBQueryException, e:
				if primary:
					self._CurrentCursor.rollbackTransaction()
					return (400, _("Database Query Exception: %s.") % e)
				else:
					raise
		if primary:
			self._CurrentCursor.commitTransaction()


	def beforeDelete(self):
		# As this is on the server side, we don't wan't to ask 'Are you sure?'
		pass
