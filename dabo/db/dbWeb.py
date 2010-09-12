#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from dabo.dLocalize import _
from dBackend import dBackend
from dbSQLite import SQLite
from dabo.lib.RemoteConnector import RemoteConnector



class Web(SQLite):
	def __init__(self):
		SQLite.__init__(self)
		self.nameEnclosureChar = "~~"
		self._remoteConnector = RemoteConnector(self)


	def getConnection(self, connectInfo, **kwargs):
		connectInfo.Database = ":memory:"
		self._connection = super(Web, self).getConnection(connectInfo, **kwargs)
		return self._connection


	def getTables(self, cursor, includeSystemTables=False):
		return self._remoteConnector.getTables(includeSystemTables=includeSystemTables)


	def getTableRecordCount(self, tableName):
		return self._remoteConnector.getTableRecordCount(tableName=tableName)


	def getFields(self, tableName, crs=None):
		return self._remoteConnector.getFields(tableName=tableName)


	def _getRemoteURL(self):
		return self._connection.connectInfo.RemoteHost

