# -*- coding: utf-8 -*-
from dabo.dLocalize import _
from dabo.dObject import dObject
from dConnectInfo import dConnectInfo
from dCursorMixin import dCursorMixin


class dConnection(dObject):
	"""Hold a connection to a backend database."""
	def __init__(self, connectInfo=None, parent=None, forceCreate=False, **kwargs):
		self._baseClass = dConnection
		self._forceCreate = forceCreate
		super(dConnection, self).__init__()
		# Store a reference to the parent object (bizobj maybe; app
		# object connection collection most likely)
		self.Parent = parent

		if connectInfo is None:
			# Fill it in from any kwargs (will get converted to a dConnectInfo
			# object in the block below).
			connectInfo = kwargs

		if isinstance(connectInfo, dConnectInfo):
			self._connectInfo = connectInfo
		elif connectInfo:
			# If they passed a cnxml file, or a dict containing valid connection info,
			# this will work fine. Otherwise, an error will be raised in the
			# dConnectInfo class.
			self._connectInfo = dConnectInfo(connInfo=connectInfo)
		else:
			raise TypeError("dConnectInfo instance or kwargs not sent.")
		self._connection = self._openConnection(**kwargs)


	def getConnection(self):
		return self._connection


	def close(self):
		self._connection.close()


	def getDictCursorClass(self):
		return self._connectInfo.getDictCursorClass()


	def getMainCursorClass(self):
		return self._connectInfo.getMainCursorClass()


	def getCursor(self, cursorClass):
		return self.getBackendObject().getCursor(cursorClass)


	def getDaboCursor(self, cursorClass=None):
		"""
		Accepts a backend-specific cursor class, mixes in the Dabo
		dCursorMixin class, and returns the result.
		"""
		if cursorClass is None:
			cursorClass = self.getDictCursorClass()
		class DaboCursor(dCursorMixin, cursorClass):
			superMixin = dCursorMixin
			superCursor = cursorClass
			def __init__(self, *args, **kwargs):
				for cls in (dCursorMixin, cursorClass):
					try:
						apply(cls.__init__, (self, ) + args, kwargs)
					except AttributeError:
						pass

		bo = self.getBackendObject()
		crs = bo.getCursor(DaboCursor)
		crs.BackendObject = bo
		# Return the AuxCursor, as it skips some of the unnecessary
		# configuration and housekeeping
		return crs.AuxCursor

	cursor = getDaboCursor


	def _openConnection(self, **kwargs):
		"""Open a connection to the database and store it for future use."""
		self.getBackendObject().KeepAliveInterval = self._connectInfo.KeepAliveInterval
		return self._connectInfo.getConnection(forceCreate=self._forceCreate, **kwargs)


	def getBackendObject(self):
		"""
		Return a reference to the connectInfo's backend-specific
		database object.
		"""
		return self._connectInfo.getBackendObject()


	def isRemote(self):
		"""
		Returns True or False, depending on whether a RemoteHost is
		specified in this connection.
		"""
		return bool(self._connectInfo.RemoteHost)


	def _getConnInfo(self):
		return self._connectInfo


	def _getName(self):
		try:
			return self.ConnectInfo.Name
		except AttributeError:
			return "?"


	ConnectInfo = property(_getConnInfo, None, None,
			_("The connectInfo for the connection.  (dConnectInfo)"))

	Name = property(_getName, None, None,
			_("The name of the connection.  (str)"))



if __name__ == "__main__":
	from dConnectInfo import dConnectInfo
	ci = dConnectInfo(DbType="MySQL")
	ci.Host = "paulmcnett.com"
	ci.Database = "dabotest"
	ci.User = "dabo"
	ci.PlainTextPassword = "dabo"

	conn = dConnection(ci).getConnection()
	cursor = conn.cursor()
	print cursor.execute("select * from recipes order by iid limit 10")
	for row in cursor.fetchall():
		print row[0], row[1]

