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
			updret = saverow(rec)
			if updret != k.UPDATE_OK:
				ret = FILE_CANCEL
				break
		return ret
	
	
	def saverow(self, rec):
		newrec =  rec.has_key(k.CURSOR_NEWFLAG)
		mem = rec[k.CURSOR_MEMENTO]
		diff = mem.makeDiff(rec, newrec)
		ret = k.UPDATE_OK
		if diff:
			if newrec:
				flds = ""
				vals = ""
				for kk, vv in diff:
					flds += ", " + kk
					vals += ", " + self.escapeQt(vv)
				sql = "insert into %s (%s) values (%s) " % (self.table, flds, vals)
				
			else:
				pkWhere = self.makePkWhere()
				updClause = self.makeUpdClause(diff)
				sql = "update %s set %s where %s" % (self.table, updClause, pkWhere)
			
			# Save off the props that will change on the update
			self.saveProps()
			#run the update
			res = self.execute(sql)
			# restore the orginal values
			self.restoreProps()
			if not res:
				ret = k.UPDATE_NORECORDS
			else:
				if newrec:
					# Need to remove the new flag
					del rec[k.CURSOR_NEWFLAG]
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
	
	
	def cancel(self, allrows=0):
		""" Reverts any changes back to the original values """
		self._errorMsg = ""
		ret = k.FILE_OK
		
		# Make sure that there is data to save
		if not self.rowcount > 0:
			self.addToErrorMsg("No data to cancel")
			return k.FILE_CANCEL
		
		if allrows:
			recs = self._rows
		else:
			recs = (self._rows[self.rownumber],)
		
		for i in range(self.rowcount, 0, -1):
			rec = self._rows[i]
			newrec =  rec.has_key(k.CURSOR_NEWFLAG)
			if newrec:
				# Discard the record, and adjust the props
				ret = self.delete(i)
			else:
				ret = cancelrow(i)
			if ret != k.FILE_OK:
				break
		return ret
	
	
	def delete(self, rownum):
		ret = k.FILE_OK
		rec = self._rows[rownum]
		newrec =  rec.has_key(k.CURSOR_NEWFLAG)
		self.saveProps(saverows=0)
		if newrec:
			tmprows = list(self._rows)
			del tmprows[rownum]
			self._rows = tuple(tmprows)
			res = 1
		else:
			pkWhere = self.makePkWhere()
			sql = "delete from %s where %s" % (self.table, pkWhere)
			res = self.execute(sql)
		
		self.restoreProps(restoreRows=0)
		if not res:
			# Nothing was deleted
			ret = FILE_CANCEL
		return ret
					
				
	def cancelrow(self, rec):
		mem = rec[k.CURSOR_MEMENTO]
	
	
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
			if fld[1] == self.STRING:
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
		return ret
		

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
				ret += fld + " = " + self.escapeQt(val) + " "
			else:
				ret += fld + " = " + str(val) + " "
		return ret


	def saveProps(self, saverows=1):
		self.tmprows = self._rows.copy()
		self.tmpcount = self.rowcount
		self.tmppos = self.rownumber
		self.tmpdesc = self.description.copy()
		

	def restoreProps(self, restorerows=1):
		if restorerows:
			self._rows = self.tmprows.copy()
		self.rowcount = len(self._rows)
		self.rownumber = min(self.tmppos, self.rowcount-1)
		self.description = self.tmpdesc.copy()
	
	
	def escapeQt(self, val):
		ret = val
		if type(val) in (types.StringType, types.UnicodeType):
			# escape and then wrap in single quotes
			sl = "\\"
			qt = "\'"
			ret = "'" + val.replace(sl, sl+sl).replace(qt, sl+qt) + "'"
		return ret			


	def addToErrorMsg(self, txt):
		""" Adds the passed text to the current error message text, 
		inserting a newline if needed """
		if txt:
			if self._errorMsg:
				self._errorMsg += "\n"
			self._errorMsg += txt


	def getErrorMsg(self):
		return self._errorMsg

		
	def isAdding(self):
		""" Returns true if the current record has the new rec flag """
		return self._rows[self.rownumber].has_attr(k.CURSOR_NEWFLAG)
	
	
	def beginTransaction(self):
		""" Implement specific calls in subclasses """
		return k.FILE_OK
	
	
	def commitTransaction(self):
		""" Implement specific calls in subclasses """
		return k.FILE_OK
	
	
	def rollbackTransaction(self):
		""" Implement specific calls in subclasses """
		return k.FILE_OK















		
