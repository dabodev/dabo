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
		tempCursor = self._connection.cursor()
		tempCursor.execute("select * from sqlite_master")
		rs = tempCursor.fetchall()
		if includeSystemTables:
			tables = [rec[1] for rec in rs
					if rec[0] == "table"]
		else:
			tables = [rec[1] for rec in rs
					if rec[0] == "table"
					and not rec[0].startswith("sqlite_")]
		return tuple(tables)
		
	def getTableRecordCount(self, tableName):
		tempCursor = self._connection.cursor()
		tempCursor.execute("select count(*) as ncount from %s" % tableName)
		return tempCursor.fetchall()[0][0]

	def getFields(self, tableName):
		tempCursor = self._connection.cursor()
		# Get the name of the PK, if any
		pkName = ""
		try:
			# If any of these statements fail, there is no valid
			# PK defined for this table.
			tempCursor.execute("select * from sqlite_master 
					where tbl_name = '%s'" 	% tableName)
			# The SQL CREATE code is in position 4 of the tuple
			tblSQL = tempCursor.fetchall()[0][4].lower()
			# Remove the CREATE...
			parenPos = tblSQL.find("(")
			tblSQL = tblSQL[parenPos:]
			pkPos = tblSQL.find("primary key")
			tblSQL = tblSQL[:pkPos]
			# The PK field name is the first word of the last
			# field def in that string
			commaPos = tblSQL.find(",")
			while commaPos > -1:
				tblSQL = tblSQL[commaPos:]
				commaPos = tblSQL.find(",")
			pkName = tblSQL.split(" ")[0]
		except:
			pass

		# Now get the field info
		tempCursor.execute("pragma table_info'%s')" % tableName)
		rs = tempCursor.fetchall()
		fields = []
		for rec in rs:
			typ = rec[2].lower()
			if typ == "integer":	
				fldType = "I"
			elif typ == "real":
				fldType = "N"
			else:
				# SQLite treats everything else as text
				fldType = "C"

			fields.append( (rec[1], fldType, rec[1].lower() == pkName)
		return tuple(fields)
