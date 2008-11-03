#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import urlparse
import sys
import os
import re
import pickle
from os.path import join as pathjoin
from zipfile import ZipFile
from cStringIO import StringIO

import dabo
import dabo.dException as dException
from dabo.dObject import dObject
from dabo.dLocalize import _
from dabo.lib.manifest import Manifest



class _RemoteConnector(object):
	"""This class handles all of the methods that will need to be carried out on 
	the server instead of locally.
	"""
	def __init__(self, fn):
		self.fn = fn
		self.fname = fn.__name__
		self._authHandler = None
		self._urlOpener = None
		super(_RemoteConnector, self).__init__()


	def __call__(self, *args, **kwargs):
		remote = bool(self.UrlBase)
		if remote:
			try:
				decFunc = getattr(self, self.fname, None)
				if decFunc:
					return decFunc(*args, **kwargs)
				else:
					# Generic remote method
					url = self._getFullUrl()
					return self._read(url)
			except urllib2.URLError, e:
				try:
					code, txt = e.reason
				except AttributeError:
					code = e.code
				if code == 500:
					# Internal server error
					dabo.errorLog.write(_("500 Internal Server Error received"))
					return
				elif code == 61:
					# Connection refused; server is down
					dabo.errorLog.write(_("\n\nThe remote server is not responding; exiting.\n\n"))
					# This could certainly be improved with a timeout loop instead of instantly quitting.
					sys.exit()
				else:
					# Some other proble; raise the error so the developer can debug
					raise e
		return self.fn(self.obj, *args, **kwargs)


	def __get__(descr, inst, instCls=None):
		descr.obj = inst
		return descr


	def _join(self, pth):
		"""Joins the path to the class's UrlBase to create a new URL."""
		return pathjoin(self.UrlBase, pth)


	def _getFullUrl(self, *args):
		ret = pathjoin(self.UrlBase, "bizservers", "biz", "%s" % hash(self.obj), self.obj.DataSource, self.fname, *args)
		return ret


	def _getManifestUrl(self, *args):
		ret = pathjoin(self.UrlBase, "manifest", *args)
		return ret


	def _read(self, url, params=None):
		if params:
			prm = urllib.urlencode(params)
		else:
			prm = None
		try:
			res = self.UrlOpener.open(url, data=prm)
		except urllib2.HTTPError, e:
			dabo.errorLog.write("HTTPError: %s" % e)
			return None
		ret = res.read()
		return ret


	def _storeEncodedDataSet(self, enc):	
		pdata, ptyps = dabo.lib.jsonDecode(enc)
		# Both values are pickled, so we need to unpickle them first
		def safeLoad(val):
			ret = None
			try:
				ret = pickle.loads(val)
			except UnicodeEncodeError, e:
				for enctype in (dabo.defaultEncoding, "utf-8", "latin-1"):
					try:
						ret = pickle.loads(val.encode(enctype))
						break
					except KeyError:
						continue
			if ret is None:
				raise UnicodeEncodeError, e
			return ret
		typs = safeLoad(ptyps)
		data = safeLoad(pdata)
		self.obj._storeData(data, typs)


	def requery(self):
		biz = self.obj
		url = self._getFullUrl()
		sql = biz.getSQL()
		# Get rid of as much unnecessary formatting as possible.
		sql = re.sub(r"\n *", " ", sql)
		sql = re.sub(r" += +", " = ", sql)
		params = {"SQL": sql, "KeyField": biz.KeyField, "_method": "GET"}
		prm = urllib.urlencode(params)
		res = self.UrlOpener.open(url, data=prm)
		encdata = res.read()
		self._storeEncodedDataSet(encdata)
	
	
	def save(self, startTransaction=False, allRows=False):
		biz = self.obj
		url = self._getFullUrl().replace(self.fname, "save")
		changes = biz.getDataDiff(allRows=allRows)
		chgDict = {hash(biz): (biz.DataSource, biz.KeyField, changes)}
		params = {"DataDiff": dabo.lib.jsonEncode(chgDict), "_method": "POST"}
		prm = urllib.urlencode(params)
		try:
			res = self.UrlOpener.open(url, data=prm)
		except urllib2.HTTPError, e:
			# There was a problem on the server side. Re-raise the appropriate
			# exception so that the UI can handle it.
			errcode = e.code
			errText = e.read()
			errMsg = "\n".join(errText.splitlines()[4:])
			if errcode == 409:
				raise dException.BusinessRuleViolation, errMsg
			elif errcode == 500:
				raise dException.ConnectionLostException, errMsg
			elif errcode == 204:
				raise dException.NoRecordsException, errMsg
			elif errcode == 400:
				raise dException.DBQueryException, errMsg
		else:
			# If successful, we need to clear the mementos. We don't need to 
			# store anything; passing None will just  clear the mementos.
			self.obj._storeData(None, None)
		

	def saveAll(self, startTransaction=True):
		self.save(startTransaction=startTransaction, allRows=True)


	def delete(self):
		biz = self.obj
		url = self._getFullUrl()
		params = {"PK": biz.getPK(), "KeyField": biz.KeyField, "_method": "DELETE"}
		prm = urllib.urlencode(params)
		res = self.UrlOpener.open(url, data=prm)
		encdata = res.read()
		self._storeEncodedDataSet(encdata)


	def syncFiles(self):
		app = self.obj
		homedir = app.HomeDirectory
		try:
			appname = file(os.path.join(homedir, ".appname")).read()
		except IOError:
			# Use the HomeDirectory name
			appname = os.path.split(homedir.rstrip("/"))[1]
		url = self._getManifestUrl(appname, "diff")
		# Get the current manifest
		currentMf = Manifest.getManifest(homedir)
		params = {"current": dabo.lib.jsonEncode(currentMf)}
		prm = urllib.urlencode(params)
		try:
			res = self.UrlOpener.open(url, data=prm)
		except urllib2.HTTPError, e:
			errcode = e.code
			errText = e.read()
			errMsg = "\n".join(errText.splitlines()[4:])
			if errcode == 304:
				# Nothing has changed on the server, so we're cool...
				return
			else:
				dabo.errorLog.write(_("HTTP Error syncing files: %s") % e)
				return
		pickleRet = res.read()
		filecode, chgs, serverMf = pickle.loads(dabo.lib.jsonDecode(pickleRet))
		# Everything after this is relative to the app's home directory, so 
		# change to it
		currdir = os.getcwd()
		os.chdir(homedir)
		# Read in the current base manifest
		try:
			baseMf = pickle.load(file(".serverManifest"))
		except IOError:
			baseMf = {}
		# Save the current server manifest
		pickle.dump(serverMf, file(".serverManifest", "w"), pickle.HIGHEST_PROTOCOL)
		# Check the server manifest for deleted files
		deleted = [pth for (pth, modf) in chgs.items()
				if not modf]
		for delpth in deleted:
			if delpth in baseMf:
				# Only delete files if they originally came from the server
				os.remove(delpth)
		# A zero filecode represents no changed files
		if filecode:
			# Request the files
			url = self._getManifestUrl(appname, "files", str(filecode))
			try:
				res = self.UrlOpener.open(url)
			except urllib2.HTTPError, e:
				dabo.errorLog.write(_("HTTP Error retrieving files: %s") % e)
			# res holds a zip file
			f = StringIO(res.read())
			zip = ZipFile(f)
			for pth in zip.namelist():
				tm = chgs.get(pth)
				dirname = os.path.split(pth)[0]
				if dirname and not os.path.exists(dirname):
					os.makedirs(dirname)
				file(pth, "wb").write(zip.read(pth))
				os.utime(pth, (tm, tm))
# NOT WORKING
# Need to find a way to handle re-importing .py files.
# 				if pth.endswith(".py"):
# 					# if this is a .py file, we want to try re-importing it
# 					modulePath = os.path.split(pth)[0].replace(os.sep, ".")
# 					thismod = os.path.splitext(pth)[0].replace(os.sep, ".")
# 					if thismod:
# 						print "THISMOD", thismod
# 						sys.modules.pop(thismod, None)
# 						__import__(thismod)
# 					if modulePath:
# 						modl = sys.modules.get(modulePath)
# 						print "pth", modulePath, type(modulePath), "MOD", modl
# 						if modl:
# 							reload(modl)
		os.chdir(currdir)


	# These are not handled by the local bizobjs, so just skip these
	def beginTransaction(self): pass
	def commitTransaction(self): pass
	def rollbackTransaction(self): pass


	def _getConnection(self):
		return self.obj._getConnection()


	def _getPassword(self):
		try:
			ci = self.Connection.ConnectInfo
			return ci.decrypt(ci.Password)
		except AttributeError:
			return ""


	def _getRemoteHost(self):
		try:
			return urlparse.urlparse(self.UrlBase)[1]
		except IndexError:
			return ""


	def _getUrlBase(self):
		try:
			ret = self.Connection.ConnectInfo.RemoteHost
		except AttributeError:
			# Might be an application object
			try:
				ret = self.obj.SourceURL
			except AttributeError:
				ret = ""
		else:
			app = dabo.dAppRef
			if app and not app.SourceURL:
				app.SourceURL = ret
		return ret


	def _getUrlOpener(self):
		if self._urlOpener is None:
			# Create an OpenerDirector with support for HTTP Digest Authentication...
			auth_handler = urllib2.HTTPDigestAuthHandler()
			auth_handler.add_password(None, self.RemoteHost, self.UserName, self.Password)
			self._urlOpener = urllib2.build_opener(auth_handler)
		return self._urlOpener


	def _getUserName(self):
		try:
			return self.Connection.ConnectInfo.User
		except AttributeError:
			return ""


	Connection = property(_getConnection, None, None,
			_("Reference to the connection object for the bizobj being decorated  (dabo.db.dConnection)"))

	Password = property(_getPassword, None, None,
			_("Plain-text password for authentication on the remote server. (str)"))

	RemoteHost = property(_getRemoteHost, None, None,
			_("Host to use as the remote server  (read-only) (str)"))

	UrlBase = property(_getUrlBase, None, None,
			_("URL for the remote server  (read-only) (str)"))

	UrlOpener = property(_getUrlOpener, None, None,
			_("Reference to the object that opens URLs and optionally authenticates.  (read-only) (urllib2.urlopener)"))

	UserName = property(_getUserName, None, None,
			_("Username for authentication on the remote server  (str)"))
