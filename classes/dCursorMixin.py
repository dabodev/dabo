from dConstants import dConstants as k
from dMemento import dMemento
import types

class dCursorMixin:
	# Name of the primary key field for this cursor. If the PK is a composite
	# (i.e., more than one field) include both separated by a comma
	keyField = ""
	# Name of the table in the database that this cursor is getting data from
	table = ""
	# SQL expression used to populate the cursor
	sql = ""
	# Holds the text of any error messages generated
	_errorMsg = ""
	# Holds the dict used for adding new blank records
	_blank = {}
	
	
	def __init__(self, sql="", *args, **kwargs):
		if sql:
			self.sql = sql
		# Check for proper values
		if not self.table or not self.sql or not self.keyField:
			self.addToErrorMsg("Critical properties have not been set:")
			if not self.table:
				self.addToErrorMsg("\t'table' ")
			if not self.sql:
				self.addToErrorMsg("\t'sql' ")
			if not self.keyField:
				self.addToErrorMsg("\t'keyField' ")
			return 0
		
	
	def first(self):
		""" Moves the record pointer to the first record of the recordset. """
		self._errorMsg = ""
		ret = k.FILE_OK
		if self.rowcount > 0:
			self.rownumber = 0
		else:
			ret = k.FILE_NORECORDS
			self.addToErrorMsg("No records in data set")
		return ret


	def prior(self):
		""" Moves the record pointer back one position in the recordset. """
		self._errorMsg = ""
		ret = k.FILE_OK
		if self.rowcount > 0:
			if self.rownumber > 0:
				self.rownumber -= 1
			else:
				ret = k.FILE_BOF
				self.addToErrorMsg("Already at the beginning of the data set.")
		else:
			ret = k.FILE_NORECORDS
			self.addToErrorMsg("No records in data set")
		return ret


	def next(self):
		""" Moves the record pointer forward one position in the recordset. """
		self._errorMsg = ""
		ret = k.FILE_OK
		if self.rowcount > 0:
			if self.rownumber < (self.rowcount-1):
				self.rownumber += 1
			else:
				ret = k.FILE_EOF
				self.addToErrorMsg("Already at the end of the data set.")
		else:
			ret = k.FILE_NORECORDS
			self.addToErrorMsg("No records in data set")
		return ret


	def last(self):
		""" Moves the record pointer to the last record in the recordset. """
		self._errorMsg = ""
		ret = k.FILE_OK
		if self.rowcount > 0:
			if self.rownumber < (self.rowcount-1):
				self.rownumber = self.rowcount-1
			else:
				ret = k.FILE_EOF
				self.addToErrorMsg("Already at the end of the data set.")
		else:
			ret = k.FILE_NORECORDS
			self.addToErrorMsg("No records in data set")
		return ret
	
	
	def save(self, allrows=0):
		self._errorMsg = ""
		ret = k.FILE_OK
		
		# Make sure that there is data to save
		if self.rowcount == 0:
			self.addToErrorMsg("No data to save")
			return k.FILE_CANCEL
		
		# Make sure that there is a PK
		if not self.checkPK():
			return k.FILE_CANCEL
		
		if allrows:
			recs = self._rows
		else:
			recs = (self._rows[self.rownumber],)
		
		for rec in recs:
			ret = saverec(rec)
			if ret != k.FILE_OK:
				break
		return ret
	
	
	def new(self):
		""" Adds a new record to the data set """
		ret = k.FILE_OK
		try:
			if not self._blank:
				self.setStructure()
			# Copy the _blank dict to the _rows, and adjust everything accordingly
			tmprows = list(self._rows)
			tmprows.append(self._blank)
			self._rows = tuple(tmprows)
			# Adjust the rowcount and position
			self.rowcount = len(self._rows)
			self.rownumber = self.rowcount - 1
			# Add the 'new record' flag to the last record (the one we just added)
			self._rows[self.rownumber][k.CURSOR_NEWFLAG] = 1
			# Add the memento
			self.addMemento(self.rownumber)
		except:
			ret = k.FILE_CANCEL
		return ret
	
	
	def setDefaults(self, vals):
		""" Called after a new record is added so that default values can be set.
		The 'vals' parameter is a dictionary of fields and their default values.
		The memento must be updated afterwards, since these should not count
		as changes to the original values. """
		row = self._rows[rownumber]
		for kk, vv in vals:
			row[kk] = vv
		row[k.CURSOR_MEMENTO].setMemento(row)
		

	def addMemento(self, rownum=-1):
		""" Adds a memento to the specified row. If the rownum is -1, it will
		add a memento to all rows """
		if rownum == -1:
			for i in range(0, self.rowcount-1):
				self.addMemento(i)
		row = self._rows[rownum]
		if not row.has_key(k.CURSOR_MEMENTO):
			row[k.CURSOR_MEMENTO] = dMemento()
		# Take the snapshot of the current values
		row[k.CURSOR_MEMENTO].setMemento(row)
		

	def setStructure(self):
		import re
		pat = re.compile("\s*select\s*.*\s*from\s*.*\s*((?:where\s(.*))+)\s*", re.I | re.M)
		if pat.search(self.sql):
			# There is a WHERE clause. Add the NODATA clause
			tmpsql = pat.sub(" where 1=0 ", self.sql)
		else:
			# no WHERE clause. See if it has GROUP BY or ORDER BY clauses
			pat = re.compile("\s*select\s*.*\s*from\s*.*\s*((?:group\s*by\s(.*))+)\s*", re.I | re.M)
			if pat.search(self.sql):
				tmpsql = pat.sub(" where 1=0 ", self.sql)
			else:				
			pat = re.compile("\s*select\s*.*\s*from\s*.*\s*((?:order\s*by\s(.*))+)\s*", re.I | re.M)
				if pat.search(self.sql):
					tmpsql = pat.sub(" where 1=0 ", self.sql)
				else:				
					# Nothing. So just tack it on the end.
					tmpsql = sql + " where 1=0 "
		
		self.execute(tmpsql)
		dscrp = self.description
		for fld in dscrp:
			fldname = fld[0]
			if fld[1] == self.STRING
				_blank[fld] = ""
			else:
				if fld[5]:
					# Float
					exec("_blank[fld] = 0." + fld[5]*"0")
				else:
					# Int
					_blank[fld] = 0
		
		
	def checkPK(self):
		""" Check to see that the field(s) specified in the keyField prop exist
		in the recordset. """
		# First, make sure that there is *something* in the field
		if not self.keyField:
			self.addToErrorMsg("Cannot save; no primary key specified")
			return 0
			
		aFields = self.keyField.split(",")
		# Make sure that there is a field with that name in the data set
		ret = 1
		try:
			for fld in aFields:
				self._rows[0][fld]
		except:
			self.addToErrorMsg("Primary key field '" + fld + "' does not exist in the data set")
			ret = 0
			break
		return ret
		
		
	
	def saverec(self, rec):
		mem = rec["dMemento"]
		diff = mem.makeDiff(rec)
		if diff:
			pkWhere = self.makePkWhere()
			updClause = self.makeUpdClause(diff)
			sql = "update %s set %s where %s" % (self.table, updClause, pkWhere)



	def makePkWhere(self):
		""" Creates the WHERE clause used for updates """
		aFields = self.keyField.split(",")
		ret = ""
		for fld in aFields:
			if ret:
				ret += " AND "
			pkVal = self._rows[self.rownumber][fld]
			if type(pkVal) == types.StringType:
				ret += fld + "='" + pkVal + "' "  
			else:
				ret += fld + "=" + str(pkVal) + " "
		return ret

	def makeUpdClause(self, diff):
		ret = ""
		for fld, val in diff:
			if ret:
				ret += ", "
			if type(val) == types.StringType:
				ret += fld + " = '" + val + "' "
			else:
				ret += fld + " = " + str(val) + " "
		return ret

















		
