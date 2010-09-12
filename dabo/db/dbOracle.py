# -*- coding: utf-8 -*-

#
# The used python database module for Oracle (cx_oracle) currently doesn't support unicode.
# So we keep this as a reference for further development only
#

import datetime
from dabo.dLocalize import _
from dBackend import dBackend
from dabo.lib.utils import ustr


class Oracle(dBackend):
	def __init__(self):
		import cx_Oracle as dbapi
		dBackend.__init__(self)
		self.dbModuleName = "cx_Oracle"
		self.dbapi = dbapi


	def getConnection(self, connectInfo, **kwargs):
		import cx_Oracle as dbapi

		self.conn_user = connectInfo.User
		port = connectInfo.Port
		if not port:
			port = 1521

		dsn = dbapi.makedsn(connectInfo.Host, port, connectInfo.Database)
		self._connection = dbapi.connect(user = connectInfo.User,
				password = connectInfo.revealPW(),
				dsn = dsn)
		return self._connection


	def getDictCursorClass(self):
		return self.dbapi.Cursor


	def escQuote(self, val):
		# escape backslashes and single quotes, and
		# wrap the result in single quotes
		sl = "\\"
		qt = "\'"
		val = val.replace(sl, sl+sl).replace(qt, sl+qt)
		return "%s%s%s" % (qt, val, qt)


	def processFields(self, txt):
		# this was used for testing only
		if isinstance(txt, unicode):
			txt = ustr(txt)
		return txt


	def formatDateTime(self, val):
		""" We need to wrap the value in quotes. """
		sqt = "'"		# single quote
		val = ustr(val)
		return "%s%s%s" % (sqt, val, sqt)


	def getTables(self, cursor, includeSystemTables=False):
		#sqlstr = "select table_name from all_tables where tablespace_name NOT IN ('SYSTEM', 'SYSAUX')"
		sqlstr = "select table_name from user_tables"
		cursor.execute(sqlstr)
		rs = cursor.getDataSet()
		tables = []
		for record in rs:
			tables.append(record[0])
		return tuple(tables)


	def getTableRecordCount(self, tableName, cursor):
		cursor.execute("select count(*) as ncount from %s" % tableName)
		return cursor.getDataSet()[0][0]


	def getFields(self, tableName, cursor):
		# get PK
		print "dbOracle.getFields(): ", tableName
		sqlstr = """SELECT cols.column_name FROM all_constraints cons, all_cons_columns cols
				WHERE cols.table_name = '%s' AND cons.constraint_type = 'P'
				AND cons.constraint_name = cols.constraint_name AND cons.owner = cols.owner
				ORDER BY cols.table_name, cols.position"""

		sqlstr = sqlstr % tableName
		cursor.execute(sqlstr)
		rs = cursor.getDataSet(rows=1)
		#print "rs = cursor.getDataSet(): ", rs
		try:
			pkField = rs[0]["COLUMN_NAME"].strip()
		except KeyError:
			pkField = None
		# Now get the field info
		sqlstr = """SELECT column_name, data_type, COALESCE(data_precision, data_length) "LENGTH",
				data_scale "SCALE" FROM all_tab_columns WHERE table_name = '%s' ORDER BY column_id"""
		cursor.execute(sqlstr % tableName)
		rs = cursor.getDataSet()
		fields = []
		for r in rs:
			fname = r["COLUMN_NAME"].strip()
			ftype = r["DATA_TYPE"].strip()
			if ftype == "NUMBER":
				if r["SCALE"] == 0:
					ft = "I"
				else:
					ft = "N"
			elif ftype == "VARCHAR2":
				ft = "M"
			elif ftype == "DATE":
				ft = "D"
			elif ftype == "TIMESTAMP(6)":
				ft = "T"
			else:
				print r
				print "unknown ftype: ", ftype
				ft = "?"
			if pkField is None:
				# No pk defined for the table
				pk = False
			else:
				pk = ( r["COLUMN_NAME"].lower() == pkField.lower() )

			fields.append((fname.lower(), ft, pk))
		return tuple(fields)


	def getLimitWord(self):
		""" Oracle uses something like "where rownum <= num". """
		return "rownum <="


	def formSQL(self, fieldClause, fromClause, joinClause,
				whereClause, groupByClause, orderByClause, limitClause):
		""" Oracle wants the limit clause as where clause. """
		if whereClause:
			if limitClause:
				whereClause = whereClause + " and %s" % limitClause
		elif limitClause:
			whereClause = "where %s" % limitClause
		clauses =  (fieldClause, fromClause, joinClause,
				whereClause, groupByClause, orderByClause)
		# clause.upper() was used for testing only
		sql = "SELECT " + "\n".join( [clause.upper() for clause in clauses if clause] )
		return sql


	def beginTransaction(self, cursor):
		""" Begin a SQL transaction."""
		ret = False
		# used for testing
		if not self._connection._has_transaction():
			self._connection.begin()
			dabo.dbActivityLog.info("SQL: begin")
			ret = True
		return ret


	def getWordMatchFormat(self):
		return """ match (%(table)s.%(field)s) against ("%(value)s") """



#
# only for testing
#
def main():
	from dabo.db.dConnectInfo import dConnectInfo

	ora = Oracle()
	connInfo = dConnectInfo(Name="myconn", DbType="Oracle", Port=1521,
			User="fwadm", Password="V7EE74E49H6BV27TA0J65G2AS21", Database="XE")
	conn = ora.getConnection(connInfo)


if __name__ == '__main__':
    main()
