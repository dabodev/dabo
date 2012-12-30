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
from dabo.dApp import dApp
from dabo.dObject import dObject
from dabo.dLocalize import _
from dabo.lib.utils import ustr
from dabo.lib.manifest import Manifest
jsonEncode = dabo.lib.jsonEncode
jsonDecode = dabo.lib.jsonDecode



class RemoteConnector(object):
	"""This class handles all of the methods that will need to be carried out on
	the server instead of locally.
	"""
	def __init__(self, obj):
		self.obj = obj
		self._baseURL = None
		self._authHandler = None
		self._urlOpener = None
		appDir = dabo.lib.utils.getUserAppDataDirectory()
		self._dataDir = pathjoin(appDir, "webapps")


	def _join(self, pth):
		"""Joins the path to the class's UrlBase to create a new URL."""
		return pathjoin(self.UrlBase, pth).replace(os.sep, "/")


	def _getFullUrl(self, mthd, *args):
		hashstr = "%s" % hash(self.obj)
		ret = pathjoin(self.UrlBase, "bizservers", "biz", hashstr, self.obj.DataSource, mthd, *args)
		ret = ret.replace(os.sep, "/")
		return ret


	def _getManifestUrl(self, *args):
		ret = pathjoin(self.UrlBase, "manifest", *args).replace(os.sep, "/")
		return ret


	def _read(self, url, params=None, reRaise=False):
		if params:
			prm = urllib.urlencode(params)
		else:
			prm = None
		try:
			res = self.UrlOpener.open(url, data=prm)
		except urllib2.HTTPError, e:
			if reRaise:
				raise
			dabo.log.error("HTTPError: %s" % e)
			return None
		ret = res.read()
		return ret


	def _storeEncodedDataSet(self, enc):
		pdata, ptyps, pstru = jsonDecode(enc)
		# The values are pickled, so we need to unpickle them first
		def safeLoad(val):
			try:
				ret = pickle.loads(val)
			except UnicodeEncodeError:
				for enctype in (dabo.getEncoding(), "utf-8", "iso8859-1"):
					try:
						ret = pickle.loads(val.encode(enctype))
					except KeyError:
						continue
					break
				else:
					raise
			return ret
		typs = safeLoad(ptyps)
		data = safeLoad(pdata)
		stru = safeLoad(pstru)
		self.obj._storeData(data, typs, stru)


	def requery(self):
		biz = self.obj
		biz.setChildLinkFilter()
		url = self._getFullUrl("requery")
		sql = biz.getSQL()

		# Get rid of as much unnecessary formatting as possible.
		sql = re.sub(r"\n *", " ", sql)
		sql = re.sub(r" += +", " = ", sql)
		sqlparams = ustr(biz.getParams())
		params = {"SQL": sql, "SQLParams": sqlparams, "KeyField": biz.KeyField, "_method": "GET"}
		prm = urllib.urlencode(params)
		try:
			res = self.UrlOpener.open(url, data=prm)
		except urllib2.HTTPError, e:
			print "ERR", e
			return
		encdata = res.read()
		self._storeEncodedDataSet(encdata)


	def save(self, startTransaction=False, allRows=False):
		biz = self.obj
		url = self._getFullUrl("save")
		chgDict = biz.getDataDiff(allRows=allRows)
		params = {"DataDiff": jsonEncode(chgDict), "_method": "POST"}
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
				raise dException.BusinessRuleViolation(errMsg)
			elif errcode == 500:
				raise dException.ConnectionLostException(errMsg)
			elif errcode == 204:
				raise dException.NoRecordsException(errMsg)
			elif errcode == 400:
				raise dException.DBQueryException(errMsg)
		else:
			# If successful, we need to clear the mementos. We don't need to
			# store anything; passing None will just  clear the mementos.
			self.obj._storeData(None, None, None)


	def saveAll(self, startTransaction=True):
		self.save(startTransaction=startTransaction, allRows=True)


	def delete(self):
		biz = self.obj
		url = self._getFullUrl("delete")
		params = {"PK": biz.getPK(), "KeyField": biz.KeyField, "_method": "DELETE"}
		prm = urllib.urlencode(params)
		res = self.UrlOpener.open(url, data=prm)
		encdata = res.read()
		self._storeEncodedDataSet(encdata)


	def deleteAll(self):
		biz = self.obj
		url = self._getFullUrl("deleteAll")
		params = {"KeyField": biz.KeyField, "_method": "DELETE"}
		prm = urllib.urlencode(params)
		res = self.UrlOpener.open(url, data=prm)
		encdata = res.read()
		self._storeEncodedDataSet(encdata)


	def launch(self, url):
		"""Check with the server for available apps if no app name is passed.
		If an app name is passed, run it directly if it exists on the server.
		"""
		# Just use the first 3 split parts.
		scheme, host, path = urlparse.urlsplit(url)[:3]
		path = path.lstrip("/")
		self._baseURL = "%s://%s" % (scheme, host)
		listURL = "%s://%s/manifest" % (scheme, host)
		res = None
		try:
			res = jsonDecode(self._read(listURL, reRaise=True))
		except urllib2.URLError, e:
			try:
				code, msg = e.reason
			except AttributeError:
				# Probably an HTTP code
				code = e.code
				msg = e.msg
			if code == 61:
				# Connection refused; server's down
				return "Error: The server is not responding. Please try later"
			elif code == 404:
				# Not a Dabo application server
				return "404 Not Found"
		except urllib2.HTTPError, e:
			print dir(e)
			errText = e.read()
			errMsg = "\n".join(errText.splitlines()[4:])
			dabo.log.error(_("HTTP Error getting app list: %s") % e)
			raise
		# If they passed an app name, and it's in the returned app list, run it
		if path and (path in res):
			return path
		else:
			return res
		# We have a list of available apps. Let the user select one
		class AppPicker(dabo.ui.dOkCancelDialog):
			def addControls(self):
				self.AutoSize = False
				self.Width = 400
				self.Height = 300
				self.Caption = _("Select Application")
				sz = self.Sizer
				lbl = dabo.ui.dLabel(self, Caption=_("The server has the following app(s):"))
				lst = dabo.ui.dListBox(self, RegID="appList")
				sz.DefaultBorder = 30
				sz.DefaultBorderSides = ["left", "right"]
				sz.DefaultSpacing = 20
				sz.append(lbl, halign="center")
				sz.append(lst, "x", halign="center")

			def setChoices(self, chc):
				self.appList.Choices = chc

		dlg = AppPicker()
		dlg.setChoices(res)
		dlg.show()
		if dlg.Accepted:
			path = dlg.appList.StringValue
		dlg.release()
		return path


	def syncFiles(self, path=None):
		app = self.obj
		if isinstance(app, dApp):
			homedir = app.HomeDirectory
			try:
				appname = file(pathjoin(homedir, ".appname")).read()
			except IOError:
				# Use the HomeDirectory name
				appname = os.path.split(homedir.rstrip("/"))[1]
		else:
			# Running from the launch method. The path will contain the app name
			appname = path
			homedir = pathjoin(self._dataDir, path)
			if not os.path.exists(homedir):
				os.makedirs(homedir)
			os.chdir(homedir)
		url = self._getManifestUrl(appname, "diff")
		# Get the current manifest
		currentMf = Manifest.getManifest(homedir)
		params = {"current": jsonEncode(currentMf)}
		prm = urllib.urlencode(params)
		try:
			res = self.UrlOpener.open(url, data=prm)
		except urllib2.HTTPError, e:
			errcode = e.code
			errText = e.read()
			errMsg = "\n".join(errText.splitlines()[4:])
			if errcode == 304:
				# Nothing has changed on the server, so we're cool...
				return homedir
			else:
				dabo.log.error(_("HTTP Error syncing files: %s") % e)
				return
		except urllib2.URLError:
			# Right now re-raise it and let the UI handle it
			raise
		nonpickleRet = res.read()
		filecode, chgs, serverMf = jsonDecode(nonpickleRet)
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
			url = self._getManifestUrl(appname, "files", ustr(filecode))
			try:
				res = self.UrlOpener.open(url)
			except urllib2.HTTPError, e:
				dabo.log.error(_("HTTP Error retrieving files: %s") % e)
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
		return homedir


	# These are not handled by the local bizobjs, so just return False
	def beginTransaction(self): return False
	def commitTransaction(self): return False
	def rollbackTransaction(self): return False


	def getFieldNames(self):
		url = self._getFullUrl("fields")
		enc = self._read(url)
		flds = jsonDecode(enc)
		return flds


	def getFieldNames(self):
		url = self._getFullUrl("fields")
		enc = self._read(url)
		flds = jsonDecode(enc)
		return flds


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
		if self._baseURL:
			# Set explicitly by the launch() method
			return self._baseURL
		app = dabo.dAppRef
		if app:
			ret = app.SourceURL
		else:
			ret = ""
		if not ret:
			# See if it's specified in the connection
			ret = self.Connection.ConnectInfo.RemoteHost
			if app:
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
