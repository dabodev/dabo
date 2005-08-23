import os
import re
import pysqlite2
from dabo.dLocalize import _
from dBackend import dBackend
from pysqlite2 import dbapi2 as dbapi

class SQLite(dBackend):
	def __init__(self):
		dBackend.__init__(self)
		self.dbModuleName = "pysqlite2"

	def getConnection(self, connectInfo):
		pth = os.path.expanduser(connectInfo.DbName)
		self._connection = dbapi.connect(pth)
		return self._connection

	def getDictCursorClass(self):
		return dbapi.Cursor

	def escQuote(self, val):
		sl = "\\"
		qt = "\'"
		return qt + val.replace(sl, sl+sl).replace(qt, qt+qt) + qt
	
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
					and not rec[1].startswith("sqlite_")]
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
			tempCursor.execute("""select * from sqlite_master 
					where tbl_name = '%s'""" 	% tableName)
			# The SQL CREATE code is in position 4 of the tuple
			tblSQL = tempCursor.fetchall()[0][4].lower()
			# Remove the CREATE...
			parenPos = tblSQL.find("(")
			tblSQL = tblSQL[parenPos+1:]
			pkPos = tblSQL.find("primary key")
			tblSQL = tblSQL[:pkPos]
			# The PK field name is the first word of the last
			# field def in that string
			commaPos = tblSQL.find(",")
			while commaPos > -1:
				tblSQL = tblSQL[commaPos:]
				commaPos = tblSQL.find(",")
			pkName = tblSQL.strip().split(" ")[0]
		except:
			pass

		# Now get the field info
		tempCursor.execute("pragma table_info('%s')" % tableName)
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

			fields.append( (rec[1], fldType, rec[1].lower() == pkName))
		return tuple(fields)


	def setNonUpdateFields(self, cursor):
		"""Use an alternative, since grabbing an empty cursor, 
		as is done in the default method, doesn't provide a 
		description. Assume that any field with the same name 
		as the fields in the base table will be updatable.
		"""
		if not cursor.Table:
			# No table specified, so no update checking is possible
			return
		# This is the current description of the cursor.
		descFlds = cursor.FieldDescription
		# Get the field info for the table
		auxCrs = cursor._getAuxCursor()
		auxCrs.execute("pragma table_info('%s')" % cursor.Table)
		rs = auxCrs._records
		
		stdFlds = [ff["name"] for ff in rs]
		# Get all the fields that are not in the table.
		cursor.__nonUpdateFields = [d[0] for d in descFlds 
				if d[0] not in [s[0] for s in stdFlds] ]
		
		
	def getUpdateTablePrefix(self, table):
		"""Table name prefixes are not allowed."""
		return ""
		
		
	def getWhereTablePrefix(self, table):
		"""Table name prefixes are not allowed."""
		return ""

	def noResultsOnSave(self):
		""" SQLite does not return anything on a successful update"""
		pass
		
	def getStructureDescription(self, cursor):
		""" Return an empty cursor description. """
		ret = ()
		# First, get the SQL
		sql = cursor.sql
		if sql:
			mtch = re.search("select\s(.+)\sfrom\s*.*", sql, re.I | re.M | re.S)
			if mtch:
				fldDescrip = []
				fldText = mtch.groups()[0].replace("\n", " ")
				flds = fldText.split(",")
				for fld in flds:
					fldDescrip.append( (fld.split(" ")[-1], "", False))
				ret = tuple(fldDescrip)
		if not ret:
			# Get the standard fields in the table
			auxCrs = cursor._getAuxCursor()
			auxCrs.execute("pragma table_info('%s')" % cursor.Table)
			rs = auxCrs._records
			fields = []
			for rec in rs:
				typ = rec["type"].lower()
				if typ == "integer":	
					fldType = "I"
				elif typ == "real":
					fldType = "N"
				else:
					# SQLite treats everything else as text
					fldType = "C"
				# We don't care about PKs here, so just make it False
				fields.append( (rec["name"], fldType, False))
			ret = tuple(fields)
		return ret

