import datetime
import kinterbasdb
from dBackend import dBackend
from dCursorMixin import dCursorMixin
import re


class Firebird(dBackend):
	def __init__(self):
		dBackend.__init__(self)
		self.dbModuleName = "kinterbasdb"
		self.fieldPat = re.compile("([A-Za-z_][A-Za-z0-9-_]+)\.([A-Za-z_][A-Za-z0-9-_]+)")


	def getConnection(self, connectInfo):
		# Port doesn't seem to work, but I need to research... for now it's disabled.
# 		port = connectInfo.Port
# 		if not port:
# 			port = 3050

		# kinterbasdb will barf with unicode strings:
		host = str(connectInfo.Host)
		user = str(connectInfo.User)
		password = str(connectInfo.revealPW())
		database = str(connectInfo.DbName)
		
		self._connection = kinterbasdb.connect(host=host, user=user, password=password,
				database=database)
		
		return self._connection
		
	def getDictCursorClass(self):
		return kinterbasdb.Cursor
	
	def noResultsOnSave(self):
		""" Firebird does not return the number of records updated, so
		we just have to ignore this, since we can't tell a failed save apart 
		from a successful one.
		"""
		return
	
	def noResultsOnDelete(self):
		""" Firebird does not return the number of records deleted, so
		we just have to ignore this, since we can't tell a failed delete apart 
		from a successful one.
		"""
		return

	def processFields(self, txt):
		""" Firebird requires that all field names be surrounded 
		by double quotes.
		"""
		return self.dblQuoteField(txt)


	def escQuote(self, val):
		# escape backslashes and single quotes, and
		# wrap the result in single quotes
		sl = "\\"
		qt = "\'"
		return qt + val.replace(sl, sl+sl).replace(qt, qt+qt) + qt
	
	def formatDateTime(self, val):
		""" We need to wrap the value in quotes. """
		sqt = "'"		# single quote
		return "%s%s%s" % (sqt, str(val), sqt)

	def getTables(self, includeSystemTables=False):
		if includeSystemTables:
			whereClause = ''
		else:
			whereClause = "where rdb$relation_name not like 'RDB$%' "
			
		tempCursor = self._connection.cursor()
		tempCursor.execute("select rdb$relation_name from rdb$relations "
			"%s order by rdb$relation_name" % whereClause)
		rs = tempCursor.fetchall()
		tables = []
		for record in rs:
			tables.append(record[0].strip())
		return tuple(tables)
		
	def getTableRecordCount(self, tableName):
		tempCursor = self._connection.cursor()
		tempCursor.execute("select count(*) as ncount from %s where 1=1" % tableName)
		return tempCursor.fetchall()[0][0]

	def getFields(self, tableName):
		tempCursor = self._connection.cursor()
		
		# Get the PK
		sql = """ select first 1 rdb$index_name
from rdb$indices
where rdb$relation_name = '%s'
and rdb$unique_flag = 1 """ % tableName.upper()
		tempCursor.execute(sql)
		rs = tempCursor.fetchone()
		try:
			pkField = rs[0].strip()
		except:
			pkField = None
		
		# Now get the field info
		sql = """  SELECT b.RDB$FIELD_NAME, d.RDB$TYPE_NAME,
 c.RDB$FIELD_LENGTH, c.RDB$FIELD_SCALE, b.RDB$FIELD_ID
 FROM RDB$RELATIONS a
 INNER JOIN RDB$RELATION_FIELDS b
 ON a.RDB$RELATION_NAME = b.RDB$RELATION_NAME
 INNER JOIN RDB$FIELDS c
 ON b.RDB$FIELD_SOURCE = c.RDB$FIELD_NAME
 INNER JOIN RDB$TYPES d
 ON c.RDB$FIELD_TYPE = d.RDB$TYPE
 WHERE a.RDB$SYSTEM_FLAG = 0
 AND d.RDB$FIELD_NAME = 'RDB$FIELD_TYPE'
 AND a.RDB$RELATION_NAME = '%s'
 ORDER BY b.RDB$FIELD_ID """ % tableName.upper()
# ORDER BY a.RDB$RELATION_NAME, b.RDB$FIELD_ID """ % tableName.upper()
 
		tempCursor.execute(sql)
		rs = tempCursor.fetchall()
		
		# This isn't fully implemented yet. We need to determine which field is the PK.
		fields = []
		for r in rs:
			name = r[0].strip()

			ftype = r[1].strip().lower()
			if ftype == "text":
				ft = "C"
			elif ftype == "varying":
				if r[2] > 64:
					ft = "M"
				else:
					ft = "C"
			elif ftype in ("long", "short", "int64", "double"):
				# Can be either integers or float types, depending on column 3
				if r[3] == 0:
					# integer
					ft = "I"
				else:
					ft = "N"
			elif ftype == "float":
				ft = "N"
			elif ftype == "date":
				ft = "D"
			elif ftype == "time":
				# Default it to character for now
				ft = "C"
			elif ftype == "timestamp":
				ft = "T"
			else:
				# BLOB
				ft = "?"
			
			pk = (name.lower() == pkField.lower() )
			
			fields.append((name.strip(), ft, pk))
			
		return tuple(fields)
	
	def flush(self, cursor):
		""" Firebird requires an explicit commit in order to have changes
		to the database written to disk.
		"""
		cursor.execute("COMMIT")
	
	def getLastInsertID(self, cursor):
		# This doesn't work - it'll return None. TODO: figure out what to do.
		# pkm: perhaps this change fixes it?
		#return self.doDefault(cursor)
		#return Firebird.doDefault(cursor)
		super(Firebird, self).getLastInsertID(cursor)

	def beginTransaction(self, cursor):
		""" Begin a SQL transaction."""
		cursor.execute("SET TRANSACTION")

	def commitTransaction(self, cursor):
		""" Commit a SQL transaction."""
		cursor.execute("COMMIT")

	def rollbackTransaction(self, cursor):
		""" Roll back (revert) a SQL transaction."""
		cursor.execute("ROLLBACK")

	def getLimitWord(self):
		""" Override the default 'limit', since Firebird doesn't use that. """
		return "first"

	def formSQL(self, fieldClause, fromClause, 
				whereClause, groupByClause, orderByClause, limitClause):
		""" Firebird wants the limit clause before the field clause.	"""
		return "\n".join( ("SELECT ", limitClause, fieldClause, fromClause, 
				whereClause, groupByClause, orderByClause) )

	def addField(self, clause, exp):
		quoted = self.dblQuoteField(exp)
		return self.addWithSep(clause, quoted)
	
	def addWhere(self, clause, exp, comp="and"):
		quoted = self.dblQuoteField(exp)
		return self.addWithSep(clause, quoted, sep=" %s " % comp)

	def setSQL(self, sql):
		return self.dblQuoteField(sql)
	def setFieldClause(self, clause):
		return self.dblQuoteField(clause)
	def setFromClause(self, clause):
		return self.dblQuoteField(clause)
	def setWhereClause(self, clause):
		return self.dblQuoteField(clause)
	def setChildFilterClause(self, clause):
		return self.dblQuoteField(clause)
	def setGroupByClause(self, clause):
		return self.dblQuoteField(clause)
	def setOrderByClause(self, clause):
		return self.dblQuoteField(clause)
		
	def dblQuoteField(self, txt):
		""" Takes a string and returns the same string with
		all occurrences of xx.yy replaced with xx."yy"
		"""
		return self.fieldPat.sub("\g<1>.\"\g<2>\"", txt)
		
