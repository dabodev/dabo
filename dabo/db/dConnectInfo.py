# -*- coding: utf-8 -*-
import random
import dabo
from dabo.lib.connParser import importConnections
from dabo.dObject import dObject
from dabo.dLocalize import _
from dabo.lib.SimpleCrypt import SimpleCrypt


class dConnectInfo(dObject):
	"""
	Holder for the properties for connecting to the backend. Each
	backend may have different names for properties, but this object
	tries to abstract that. The value stored in the Password must be
	encrypted in the format set in the app. This class has  'encrypt' and
	'decrypt' functions for doing this, or you can set the PlainTextPassword
	property, and the class will encypt that value and set the Password
	property for you.

	You can create it in several ways, like most Dabo objects. First, you
	can pass all the settings as parameters to the constructor::

		ci = dConnectInfo(DbType="MySQL", Host="domain.com",
			User="daboUser", PlainTextPassword="secret", Port=3306,
			Database="myData", Name="mainConnection")

	Or you can create a dictionary of the various props, and pass that
	in the 'connInfo' parameter::

		connDict = {"DbType" : "MySQL", "Host" : "domain.com",
			"User" : "daboUser", "PlainTextPassword" : "secret",
			"Port" : 3306, "Database" : "myData", "Name" : "mainConnection"}
		ci = dConnectInfo(connInfo=connDict)

	Or you can create the object and then set the props
	individually::

		ci = dConnectInfo()
		ci.DbType = "MySQL"
		ci.Host = "domain.com"
		ci.User = "daboUser"
		ci.PlainTextPassword = "secret"
		ci.Database = "myData"
		ci.Name = "mainConnection"

	If you are running a remote app, should set the RemoteHost property instead of Host. The
	DbType will be "web".
	"""
	def __init__(self, connInfo=None, **kwargs):
		self._baseClass = dConnectInfo
		self._backendObject = None
		self._host = self._user = self._password = self._dbType = self._database = self._port = self._name = self._remoteHost = ""
		self._keepAliveInterval = None
		super(dConnectInfo, self).__init__(**kwargs)
		if connInfo:
			self.setConnInfo(connInfo)


	def setConnInfo(self, connInfo, nm=""):
		# Run through the connDict, and set the appropriate properties. If it isn't
		# a valid property name, raise TypeError.
		self._customParameters = {}
		props = ["Name", "DbType", "Host", "User", "Password", "Database",
				"PlainTextPassword", "Port", "RemoteHost", "KeepAliveInterval"]
		lprops = [p.lower() for p in props]
		for k, v in connInfo.items():
			try:
				propidx = lprops.index(k.lower())
			except ValueError:
				propidx = None
			if propidx is not None:
				setattr(self, props[propidx], v)
			else:
				self._customParameters[k] = v


	def getConnection(self, **kwargs):
		kwargs.update(self.CustomParameters)
		return self._backendObject.getConnection(self, **kwargs)


	def getDictCursorClass(self):
		try:
			return self._backendObject.getDictCursorClass()
		except TypeError:
			return None


	def getMainCursorClass(self):
		try:
			return self._backendObject.getMainCursorClass()
		except TypeError:
			return None


	def encrypt(self, val):
		if self.Application:
			return self.Application.encrypt(val)
		else:
			return self.Crypto.encrypt(val)


	def decrypt(self, val):
		if self.Application:
			return self.Application.decrypt(val)
		else:
			return self.Crypto.decrypt(val)


	def revealPW(self):
		return self.decrypt(self.Password)


	def getBackendObject(self):
		return self._backendObject


	def _getCrypto(self):
		try:
			ret = self.Application.Crypto
		except AttributeError:
			try:
				ret = self._cryptoProvider
			except AttributeError:
				ret = self._cryptoProvider = None
		if ret is None:
			# Use the default crypto
			ret = self._cryptoProvider = SimpleCrypt()
		return self._cryptoProvider

	def _setCrypto(self, val):
		self._cryptoProvider = val


	def _getCustomParameters(self):
		try:
			return self._customParameters.copy()
		except AttributeError:
			return {}


	def _getDbType(self):
		try:
			return self._dbType
		except AttributeError:
			return None

	def _setDbType(self, dbType):
		"""Set the backend type for the connection if valid."""
		_oldObject = self._backendObject
		# As other backends are coded into the framework, we will need
		# to expand the if/elif list.
		if dbType is not None:
			# Evaluate each type of backend
			nm = dbType.lower()
			try:
				if nm == "mysql":
					import dbMySQL
					self._backendObject = dbMySQL.MySQL()
				elif nm == "sqlite":
					import dbSQLite
					self._backendObject = dbSQLite.SQLite()
				elif nm == "firebird":
					import dbFirebird
					self._backendObject = dbFirebird.Firebird()
				elif nm == "postgresql":
					import dbPostgreSQL
					self._backendObject = dbPostgreSQL.Postgres()
				elif nm == "mssql":
					import dbMsSQL
					self._backendObject = dbMsSQL.MSSQL()
				elif nm == "oracle":
					import dbOracle
					self._backendObject = dbOracle.Oracle()
				elif nm == "web":
					import dbWeb
					self._backendObject = dbWeb.Web()
				elif nm == "odbc":
					import dbODBC
					self._backendObject = dbODBC.ODBC()
				else:
					raise ValueError("Invalid database type: %s." % nm)
			except ImportError:
				dabo.log.error(_("You do not have the database module for %s installed") % dbType)
				self._dbType = None
				self._backendObject = None
			if _oldObject != self._backendObject:
				self._dbType = dbType
		else:
			self._dbType = None
			self._backendObject = None


	def _getDatabase(self):
		return self._database

	def _setDatabase(self, database):
		self._database = database


	def _getHost(self):
		return self._host

	def _setHost(self, host):
		self._host = host


	def _getKeepAliveInterval(self):
		return self._keepAliveInterval

	def _setKeepAliveInterval(self, val):
		if not val:
			val = None
		else:
			val = int(val)
		self._keepAliveInterval = val


	def _getName(self):
		return self._name

	def _setName(self, val):
		self._name = val


	def _getPassword(self):
		return self._password

	def _setPassword(self, password):
		self._password = password


	def _setPlainPassword(self, val):
		self._password = self.encrypt(val)


	def _getPort(self):
		return self._port

	def _setPort(self, port):
		try:
			self._port = int(port)
		except ValueError:
			self._port = None


	def _getRemoteHost(self):
		return self._remoteHost

	def _setRemoteHost(self, host):
		self._remoteHost = host


	def _getUser(self):
		return self._user

	def _setUser(self, user):
		self._user = user



	Crypto = property(_getCrypto, _setCrypto, None,
			_("""Reference to the object that provides cryptographic services if run
			outside of an application.  (varies)"""))

	CustomParameters = property(_getCustomParameters, None, None,
			_("""Additional parameters passed to backend object connect method. (dict)"""))

	DbType = property(_getDbType, _setDbType, None,
			_("Name of the backend database type.  (str)"))

	Database = property(_getDatabase, _setDatabase, None,
			_("The database name to login to. (str)"))

	Host = property(_getHost, _setHost, None,
			_("The host name or ip address. (str)"))

	KeepAliveInterval = property(_getKeepAliveInterval, _setKeepAliveInterval, None,
			_("""Specifies how often a KeepAlive query should be sent to the server. (int)

			Defaults to None, meaning we never send a KeepAlive query. The interval
			is expressed in seconds.
			"""))

	Name = property(_getName, _setName, None,
			_("The name used to reference this connection. (str)"))

	Password = property(_getPassword, _setPassword, None,
			_("The encrypted password of the user. (str)"))

	PlainTextPassword = property(None, _setPlainPassword, None,
			_("""Write-only property that encrypts the value and stores that
				in the Password property. (str)"""))

	Port = property(_getPort, _setPort, None,
			_("The port to connect on (may not be applicable for all databases). (int)"))

	RemoteHost = property(_getRemoteHost, _setRemoteHost, None,
			_("When running as a web app, this holds the host URL. (str)"))

	User = property(_getUser, _setUser, None,
			_("The user name. (str)"))


if __name__ == "__main__":
	test = dConnectInfo()
	print test.DbType
	test.DbType = "MySQL"
	print test.DbType
	test.DbType = "SQLite"
	print test.DbType

