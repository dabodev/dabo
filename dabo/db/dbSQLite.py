import datetime
import pysqlite2
from dabo.dLocalize import _
from dBackend import dBackend

class SQLite(dBackend):
	def __init__(self):
		dBackend.__init__(self)
		self.dbModuleName = "pysqlite2"

	def getConnection(self, connectInfo):
		from pysqlite2 import dbapi2 as dbapi
		self._connection = dbapi.connect(connectInfo.DbName)
		return self._connection

	def getDictCursorClass(self):
		#### TODO: Replace with appropriate SQLite dbapi module class
		####   or just a standard cursor, if it doesn't offer Dict cursors.
		return pysqlite2.Cursor

	def escQuote(self, val):
		#### TODO: Verify that SQLite uses this method for escaping quotes
		# escape backslashes and single quotes, and
		# wrap the result in single quotes
		sl = "\\"
		qt = "\'"
		return qt + val.replace(sl, sl+sl).replace(qt, sl+qt) + qt
	
	def formatDateTime(self, val):
		""" We need to wrap the value in quotes. """
		#### TODO: Make sure that the format for DateTime 
		####    values is returned correctly 
		sqt = "'"		# single quote
		return "%s%s%s" % (sqt, str(val), sqt)
		
	def getTables(self, includeSystemTables=False):
		#### TODO: Verify that this works with SQLite, including
		####    the option for including/excluding system tables.
		tempCursor = self._connection.cursor()
		tempCursor.execute("show tables")
		rs = tempCursor.fetchall()
		tables = []
		for record in rs:
			tables.append(record[0])
		return tuple(tables)
		
	def getTableRecordCount(self, tableName):
		#### TODO: Verify that this is the correct syntax for SQLite
		tempCursor = self._connection.cursor()
		tempCursor.execute("select count(*) as ncount from %s" % tableName)
		return tempCursor.fetchall()[0][0]

	def getFields(self, tableName):
		tempCursor = self._connection.cursor()
		#### TODO: Modify for SQLite syntax
		tempCursor.execute("describe %s" % tableName)
		rs = tempCursor.fetchall()
		fldDesc = tempCursor.description
		# The field name is the first element of the tuple. Find the
		# first entry with the field name 'Key'; that will be the 
		# position for the PK flag
		for i in range(len(fldDesc)):
			if fldDesc[i][0] == 'Key':
				pkPos = i
				break
		
		fields = []
		for r in rs:
			#### TODO: Alter these so that they match the field type
			####    names returned by SQLite.
			name = r[0]
			ft = r[1]
			if ft.split()[0] == "tinyint(1)":
				ft = "B"
			elif "int" in ft:
				ft = "I"
			elif "varchar" in ft:
				# will be followed by length
				ln = int(ft.split("(")[1].split(")")[0])
				if ln > 255:
					ft = "M"
				else:
					ft = "C"
			elif "char" in ft :
				ft = "C"
			elif "text" in ft:
				ft = "M"
			elif "decimal" in ft:
				ft = "N"
			elif "datetime" in ft:
				ft = "T"
			elif "date" in ft:
				ft = "D"
			elif "enum" in ft:
				ft = "C"
			else:
				ft = "?"
			pk = (r[pkPos] == "PRI")
			
			fields.append((name.strip(), ft, pk))
		return tuple(fields)
