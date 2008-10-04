#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from dabo.dLocalize import _
from dBackend import dBackend
from dbSQLite import SQLite
from dabo.lib.RemoteConnector import _RemoteConnector as remote



class Web(SQLite):
	def __init__(self):
		SQLite.__init__(self)
		self.nameEnclosureChar = "~~"


	def getConnection(self, connectInfo, **kwargs):
		connectInfo.Database = ":memory:"
		self._connection = super(Web, self).getConnection(connectInfo, **kwargs)
		return self._connection


	@remote
	def getTables(self, includeSystemTables=False):
		raise ValueError, _("Table listing must come from web service")
		

	def getTableRecordCount(self, tableName):
		raise ValueError, _("Record Count must come from web service")


	@remote
	def getFields(self, tableName, crs=None):
		raise ValueError, _("Field listing must come from web service")


	def _getRemoteURL(self):
		return self._connection.connectInfo.RemoteHost

