import types, datetime, inspect

import dabo
import dabo.dConstants as k
from dabo.db.dMemento import dMemento
from dabo.dLocalize import _
import dabo.dException as dException
import dabo.common

class dCursorMixin(dabo.common.dObject):
	# SQL expression used to populate the cursor
	sql = ""
	# Holds the dict used for adding new blank records
	_blank = {}
	# Last executed sql statement
	lastSQL = ""
	# Last executed sql params
	lastParams = None
	# Column on which the result set is sorted
	sortColumn = ""
	# Order of the sorting. Should be either ASC, DESC or empty for no sort
	sortOrder = ""
	# Is the sort case-sensitive?
	sortCase = True
	# Holds the keys in the original, unsorted order for unsorting the dataset
	__unsortedRows = []
	# Holds the name of fields to be skipped when updating the backend, such
	# as calculated or derived fields, or fields that are otherwise not to be updated.
	__nonUpdateFields = []
	# User-editable list of non-updated fields
	nonUpdateFields = []
	# Default encoding
	__encoding = "latin-1"
	
	
	def __init__(self, sql="", *args, **kwargs):
		if sql:
			self.sql = sql
			
		#dCursorMixin.doDefault()
		super(dCursorMixin, self).__init__()
		
		self._blank = {}
		self.__unsortedRows = []
		self.__nonUpdateFields = []
		self.nonUpdateFields = []
		self.__tmpPK = -1		# temp PK value for new records.
		# Initialize the saved props stack.
		self.holdrows = []
		self.holdcount = []
		self.holdpos = []
		self.holddesc = []
		# Reference to the object with backend-specific behaviors
		self.__backend = None
		
		# properties for the SQL Builder functions
		self._fieldClause = ""
		self._fromClause = ""
		self._whereClause = ""
		self._childFilterClause = ""
		self._groupByClause = ""
		self._orderByClause = ""
		self._limitClause = ""
		self._defaultLimit = 1000
		self.hasSqlBuilder = True

		# Just in case this is used outside of the context of a bizobj
		if not hasattr(self, "superCursor") or self.superCursor is None:
			myBases = self.__class__.__bases__
			for base in myBases:
				# Find the first base class that doesn't have the 'autoPopulatePK'
				# attribute. Designate that class as the superCursor class.
				if hasattr(base, "fetchall"):
					self.superCursor = base
					break


	def setSQL(self, sql):
		self.sql = sql


	def getSortColumn(self):
		return self.sortColumn


	def getSortOrder(self):
		return self.sortOrder


	def getSortCase(self):
		return self.sortCase


	def execute(self, sql, params=()):
		"""
		The idea here is to let the super class do the actual work in retrieving the data. However, 
		many cursor classes can only return row information as a list, not as a dictionary. This
		method will detect that, and convert the results to a dictionary.
		"""
		# Some backends, notably Firebird, require that fields be specially
		# marked.
		sql = self.processFields(sql)
		
		# Make sure all Unicode charcters are properly encoded.
		if type(sql) == types.UnicodeType:
			sqlEX = sql.encode(self.__encoding)
		else:
			sqlEX = sql

		if params is None or len(params) == 0:
			res = self.superCursor.execute(self, sqlEX)
		else:
			res = self.superCursor.execute(self, sqlEX, params)
		
		# Not all backends support 'fetchall' after executing a query
		# that doesn't return records, such as an update.
		try:
			self._records = self.fetchall()
		except:
			pass
		
		if self.RowCount > 0:
			self.RowNumber = max(self.RowNumber, 0, (self.RowCount-1) )

		if self._records:
			if type(self._records[0]) == types.TupleType:
				# Need to convert each row to a Dict
				tmpRows = []
				# First, get the description property and extract the field names from that
				fldNames = []
				for fld in self.description:
					fldNames.append(fld[0].lower())
				fldcount = len(fldNames)
				# Now go through each row, and convert it to a dictionary. We will then
				# add that dictionary to the tmpRows list. When all is done, we will replace 
				# the _records property with that list of dictionaries
				for row in self._records:
					dic= {}
					for i in range(0, fldcount):
						if type(row[i]) == type(""):	
							# String; convert it to unicode
							dic[fldNames[i]] = unicode(row[i], self.__encoding)
						else:
							dic[fldNames[i]] = row[i]
					tmpRows.append(dic)
				self._records = tuple(tmpRows)

			else:
				# Make all string values into unicode
				for row in self._records:
					for fld in row.keys():
						val = row[fld]
						if type(val) == type(""):	
							# String; convert it to unicode
							row[fld]= unicode(val, self.__encoding)
		return res
	
	
	def requery(self, params=None):
		self.lastSQL = self.sql
		self.lastParams = params
		
		if not self.sql:
			# Don't run an empty SQL statement!
			self.sql = self.getSQL()
		
		self.execute(self.sql, params)
		# Add mementos to each row of the result set
		self.addMemento(-1)

		# Check for any derived fields that should not be included in 
		# any updates.
		self.__setNonUpdateFields()

		# Clear the unsorted list, and then apply the current sort
		self.__unsortedRows = []
		if self.sortColumn:
			try:
				self.sort(self.sortColumn, self.sortOrder)
			except dException.NoRecordsException, e:
				# No big deal
				pass
		return True


	def sort(self, col, dir=None, caseSensitive=True):
		""" Sort the result set on the specified column in the specified order.

		If the sort direction is not specified, sort() cycles among Ascending, 
		Descending and no sort order.
		"""
		currCol = self.sortColumn
		currOrd = self.sortOrder
		currCase = self.sortCase

		# Check to make sure that we have data
		if self.RowCount < 1:
			raise dException.NoRecordsException, _("No rows to sort.")

		# Make sure that the specified column is a column in the result set
		if not self._records[0].has_key(col):
			raise dException.dException, _("Invalid column specified for sort: ") + col

		newCol  = col
		if col == currCol:
			# Not changing the column; most likely they are flipping 
			# the sort order.
			if (dir is None) or not dir:
				# They didn't specify the sort. Cycle through the sort orders
				if currOrd == "ASC":
					newOrd = "DESC"
				elif currOrd == "DESC":
					newOrd = ""
				else:
					newOrd = "ASC"
			else:
				if dir.upper() in ("ASC", "DESC", ""):
					newOrd = dir.upper()
				else:
					raise dException.dException, _("Invalid Sort direction specified: ") + dir

		else:
			# Different column specified.
			if (dir is None) or not dir:
				# Start in ASC order
				newOrd = "ASC"
			else:
				if dir.upper() in ("ASC", "DESC", ""):
					newOrd = dir.upper()
				else:
					raise dException.dException, _("Invalid Sort direction specified: ") + dir
		self.__sortRows(newCol, newOrd, caseSensitive)
		# Save the current sort values
		self.sortColumn = newCol
		self.sortOrder = newOrd
		self.sortCase = caseSensitive


	def __sortRows(self, col, ord, caseSensitive):
		""" Sort the rows of the cursor.

		At this point, we know we have a valid column and order. We need to 
		preserve the unsorted order if we haven't done that yet; then we sort
		the data according to the request.
		"""
		if not self.__unsortedRows:
			# Record the PK values
			for row in self._records:
				self.__unsortedRows.append(row[self.KeyField])

		# First, preserve the PK of the current row so that we can reset
		# the RowNumber property to point to the same row in the new order.
		currRowKey = self._records[self.RowNumber][self.KeyField]
		# Create the list to hold the rows for sorting
		sortList = []
		if not ord:
			# Restore the rows to their unsorted order
			for row in self._records:
				sortList.append([self.__unsortedRows.index(row[self.KeyField]), row])
		else:
			for row in self._records:
				sortList.append([row[col], row])
		# At this point we have a list consisting of lists. Each of these member
		# lists contain the sort value in the zeroth element, and the row as
		# the first element.
		# First, see if we are comparing strings
		compString = type(sortList[0][0]) in (types.StringType, types.UnicodeType)
		if compString and not caseSensitive:
			# Use a case-insensitive sort.
			sortList.sort(lambda x, y: cmp(x[0].lower(), y[0].lower()))
		else:
			sortList.sort()

		# Unless DESC was specified as the sort order, we're done sorting
		if ord == "DESC":
			sortList.reverse()
		# Extract the rows into a new list, then convert them back to the _records tuple
		newRows = []
		for elem in sortList:
			newRows.append(elem[1])
		self._records = tuple(newRows)

		# restore the RowNumber
		for i in range(0, self.RowCount):
			if self._records[i][self.KeyField] == currRowKey:
				self.RowNumber = i
				break


	def setNonUpdateFields(self, fldList=[]):
		self.nonUpdateFields = fldList
	
	
	def getNonUpdateFields(self):
		return self.nonUpdateFields + self.__nonUpdateFields
		
		
	def __setNonUpdateFields(self):
		# First, save off the current state.
		self.__saveProps()

		# This is the current description of the cursor.
		descFlds = self.description
		# Get the raw version of the table
		sql = """select * from %s where 1=0 """ % self.Table
		self.execute( sql )
		# This is the clean version of the table.
		stdFlds = self.description

		# Restore the original state of the cursor; we have everything
		# we need to determine the non-update fields.
		self.__restoreProps()

		# Get all the fields that are not in the table.
		self.__nonUpdateFields = [d[0] for d in descFlds 
				if d[0] not in [s[0] for s in stdFlds] ]
		# Extract the remaining fields (no need to test any already excluded
		remFlds = [ d for d in descFlds if d[0] not in self.__nonUpdateFields ]
		
		# Now add any for which the members (except the display value, 
		# which is in position 2) do not match
		self.__nonUpdateFields += [ b[0] for b in remFlds 
				for s in [z for z in stdFlds if z[0] == b[0] ]
				if (b[1] != s[1]) or (b[3] != s[3]) or (b[4] != s[4]) 
				or (b[5] != s[5]) or (b[6] != s[6]) ]
	

	def isChanged(self, allRows=True):
		""" 	Scan all the records and compare them with their mementos. 
		Returns True if any differ, False otherwise.
		"""
		ret = False

		if self.RowCount > 0:
			if allRows:
				recs = self._records
			else:
				recs = (self._records[self.RowNumber],)

			for i in range(len(recs)):
				rec = recs[i]
				if self.isRowChanged(rec):
					ret = True
					break
		return ret


	def isRowChanged(self, rec):
		ret = False
		if rec.has_key(k.CURSOR_MEMENTO):
			mem = rec[k.CURSOR_MEMENTO]
			newrec = rec.has_key(k.CURSOR_NEWFLAG)
			ret = newrec or mem.isChanged(rec)
		return ret


	def setMemento(self):
		if self.RowCount > 0:
			if (self.RowNumber >= 0) and (self.RowNumber < self.RowCount):
				self.addMemento(self.RowNumber)
	
	
	def genTempAutoPK(self):
		""" Create a temporary PK for a new record. Set the key field to this
		value, and also create a temp field to hold it so that when saving the
		new record, child records that are linked to this one can be updated
		with the actual PK value.
		"""
		rec = self._records[self.RowNumber]
		tmpPK = self._genTempPKVal()
		rec[self.KeyField] = tmpPK
		rec[k.CURSOR_TMPKEY_FIELD] = tmpPK
		
	
	
	def _genTempPKVal(self):
		""" Return the next available temp PK value. It will be a string, and 
		postfixed with '-dabotmp' to avoid potential conflicts with actual PKs
		"""
		tmp = self.__tmpPK
		# Decrement the temp PK value
		self.__tmpPK -= 1
		return str(tmp) + "-dabotmp"
	
	
	def getPK(self):
		""" Returns the value of the PK field in the current record. If that record
		is new an unsaved record, return the temp PK value
		"""
		ret = None
		if self.RowCount <= 0:
			raise dException.NoRecordsException, _("No records in the data set.")
		rec = self._records[self.RowNumber]
		if rec.has_key(k.CURSOR_NEWFLAG):
			# New, unsaved record
			return rec[k.CURSOR_TMPKEY_FIELD]


	def getFieldVal(self, fld):
		""" Return the value of the specified field.
		"""
		ret = None
		if self.RowCount <= 0:
			raise dException.NoRecordsException, _("No records in the data set.")

		rec = self._records[self.RowNumber]
		if rec.has_key(fld):
			ret = rec[fld]
		else:
			raise dException.dException, "%s '%s' %s" % (
						_("Field"),
						fld,
						_("does not exist in the data set"))
		return ret


	def setFieldVal(self, fld, val):
		""" Set the value of the specified field. 
		"""
		if self.RowCount <= 0:
			raise dException.dException, _("No records in the data set")
		else:
			rec = self._records[self.RowNumber]
			if rec.has_key(fld):
				if type(rec[fld]) != type(val):
					if ( type(val) in (types.UnicodeType, types.StringType) 
							and type(rec[fld]) in (types.UnicodeType, types.StringType) ):
						if type(rec[fld]) == types.StringType:
							val = str(val)
						else:
							val = unicode(val)
					elif type(rec[fld]) == type(int()) and type(val) == type(bool()):
						# convert bool to int (original field val was int, but UI
						# changed to int. 
						val = int(val)
				if type(rec[fld]) != type(val):
					ignore = False
					# Date and DateTime types are handled as character, even if the 
					# native field type is not. Ignore these
					dtStrings = ("<type 'DateTime'>", "<type 'Date'>")
					if str(type(rec[fld])) in dtStrings:
						if type(val) in (type(""), type(u"")):
							ignore = True
					
					else:
						# This can also happen with a new record, since we just stuff the
						# fields full of empty strings.
						ignore = self._records[self.RowNumber].has_key(k.CURSOR_NEWFLAG)
					
					if not ignore:
						msg = "!!! Data Type Mismatch: field=" + fld + ". Expecting:" + str(type(rec[fld])) + "; got:" + str(type(val))
						dabo.errorLog.write(msg)
					
				rec[fld] = val

			else:
				raise dException.dException, "%s '%s' %s" % ( _("Field"),
							fld, _("does not exist in the data set") 	)


	def getRecordStatus(self, rownum=None):
		""" Returns a dictionary containing an element for each changed 
		field in the specified record (or the current record if none is specified).
		The field name is the key for each element; the value is a 2-element
		tuple, with the first element being the original value, and the second 
		being the current value.
		"""
		if rownum is None:
			rownum = self.RowNumber
		try:
			row = self._records[RowNumber]
			mem = row[k.CURSOR_MEMENTO]
		except:
			# Either there isn't any such row number, or it doesn't have a 
			# memento. Either way, return an empty dict
			return {}
		diff = mem.makeDiff(row, isNewRecord=row.has_key(k.CURSOR_NEWFLAG))
		ret = {}
		for kk, vv in diff:
			ret[kk] = (mem.getOrigVal(kk), vv)
		return ret
			
		return self.Cursor.getRecordStatus(rownum)


	def getDataSet(self):
		""" Get the entire data set encapsulated in a tuple.
		"""
		try:
			return self._records
		except AttributeError:
			return ()


	def getRowCount(self):
		""" Get the row count of the current data set.
		
		Redundant: Just get this from the property RowCount.
		"""
		return self.RowCount


	def getRowNumber(self):
		""" Get the active row number of the data set.
		
		Redundant: Just get this from the property RowNumber.
		"""
		return self.RowNumber


	def first(self):
		""" Move the record pointer to the first record of the data set. 
		"""
		if self.RowCount > 0:
			self.RowNumber = 0
		else:
			raise dException.NoRecordsException, _("No records in data set")


	def prior(self):
		""" Move the record pointer back one position in the recordset.
		"""
		if self.RowCount > 0:
			if self.RowNumber > 0:
				self.RowNumber -= 1
			else:
				raise dException.BeginningOfFileException, _("Already at the beginning of the data set.")
		else:
			raise dException.NoRecordsException, _("No records in data set")


	def next(self):
		""" Move the record pointer forward one position in the recordset.
		"""
		if self.RowCount > 0:
			if self.RowNumber < (self.RowCount-1):
				self.RowNumber += 1
			else:
				raise dException.EndOfFileException, _("Already at the end of the data set.")
		else:
			raise dException.NoRecordsException, _("No records in data set")


	def last(self):
		""" Move the record pointer to the last record in the recordset.
		"""
		if self.RowCount > 0:
			self.RowNumber = self.RowCount-1
		else:
			raise dException.NoRecordsException, _("No records in data set")


	def save(self, allrows=False):
		""" Save any changes to the data back to the data store.
		"""
		# Make sure that there is data to save
		if self.RowCount <= 0:
			raise dException.dException, _("No data to save")

		# Make sure that there is a PK
		self.checkPK()

		if allrows:
			recs = self._records
		else:
			recs = (self._records[self.RowNumber],)

		for rec in recs:
			self.__saverow(rec)


	def __saverow(self, rec):
		newrec =  rec.has_key(k.CURSOR_NEWFLAG)
		mem = rec[k.CURSOR_MEMENTO]
		diff = self.makeUpdDiff(rec, newrec)

		if diff:
			if newrec:
				flds = ""
				vals = ""
				
				for kk, vv in diff.items():
					if self.AutoPopulatePK and (kk == self.KeyField):
						# we don't want to include the PK in the insert
						continue
					if kk in self.getNonUpdateFields():
						# Skip it.
						continue
						
					# Append the field and its value.
					flds += ", " + kk
					
					# add value to expression
					if type(vv) == type(datetime.date(1,1,1)):
						# Some databases have specific rules for formatting date values.
						vals += ", " + self.formatDateTime(vv)
					else:
						vals += ", " + str(self.escQuote(vv))
				# Trim leading comma-space from the strings
				flds = flds[2:]
				vals = vals[2:]
				sql = "insert into %s (%s) values (%s) " % (self.Table, flds, vals)

			else:
				pkWhere = self.makePkWhere(rec)
				updClause = self.makeUpdClause(diff)
				sql = "update %s set %s where %s" % (self.Table, updClause, pkWhere)
			
			# Save off the props that will change on the update
			self.__saveProps()
			#run the update
			res = self.execute(sql)
			
			if newrec and self.AutoPopulatePK:
				# Call the database backend-specific code to retrieve the
				# most recently generated PK value.
				newPKVal = self.getLastInsertID()
			# restore the orginal values
			self.__restoreProps()

			if newrec and self.AutoPopulatePK:
				self.setFieldVal(self.KeyField, newPKVal)

			if newrec:
				# Need to remove the new flag
				del rec[k.CURSOR_NEWFLAG]
			else:
				if not res:
					# Different backends may cause res to be None
					# even if the save is successful.
					self.BackendObject.noResultsOnSave()

	
	def makeUpdDiff(self, rec, isnew=False):
		mem = rec[k.CURSOR_MEMENTO]
		ret = mem.makeDiff(rec, isnew)
		for fld in self.getNonUpdateFields():
			if ret.has_key(fld):
				del ret[fld]
		return ret
		
		

	def new(self):
		""" Add a new record to the data set.
		"""
		if not self._blank:
			self.__setStructure()
		# Copy the _blank dict to the _records, and adjust everything accordingly
		tmprows = list(self._records)
		tmprows.append(self._blank.copy())
		self._records = tuple(tmprows)
		# Adjust the RowCount and position
		self.RowNumber = self.RowCount - 1
		# Add the 'new record' flag to the last record (the one we just added)
		self._records[self.RowNumber][k.CURSOR_NEWFLAG] = True
		# Add the memento
		self.addMemento(self.RowNumber)


	def cancel(self, allrows=False):
		""" Revert any changes to the data set back to the original values.
		"""
		# Make sure that there is data to save
		if not self.RowCount > 0:
			raise dException.dException, _("No data to cancel")

		if allrows:
			recs = self._records
		else:
			recs = (self._records[self.RowNumber],)

		# Create a list of PKs for each 'eligible' row to cancel
		cancelPKs = []
		for rec in recs:
			cancelPKs.append(rec[self.KeyField])

		for i in range(self.RowCount-1, -1, -1):
			rec = self._records[i]

			if rec[self.KeyField] in cancelPKs:
				if not self.isRowChanged(rec):
					# Nothing to cancel
					continue

				newrec =  rec.has_key(k.CURSOR_NEWFLAG)
				if newrec:
					# Discard the record, and adjust the props
					self.delete(i)
				else:
					self.__cancelRow(rec)


	def __cancelRow(self, rec):
		mem = rec[k.CURSOR_MEMENTO]
		diff = mem.makeDiff(rec)
		if diff:
			for fld, val in diff.items():
				rec[fld] = mem.getOrigVal(fld)


	def delete(self, delRowNum=None):
		""" Delete the specified row. If no row specified, 
		delete the currently active row.
		"""
		if self.RowNumber < 0 or self.RowCount == 0:
			# No query has been run yet
			raise dException.NoRecordsException, _("No record to delete")
		if delRowNum is None:
			# assume that it is the current row that is to be deleted
			delRowNum = self.RowNumber

		rec = self._records[delRowNum]
		newrec =  rec.has_key(k.CURSOR_NEWFLAG)
		self.__saveProps(saverows=False)
		if newrec:
			tmprows = list(self._records)
			del tmprows[delRowNum]
			self._records = tuple(tmprows)
			res = True
		else:
			pkWhere = self.makePkWhere()
			sql = "delete from %s where %s" % (self.Table, pkWhere)
			res = self.execute(sql)

		if res:
			# First, delete the row from the held properties
			topOfStack = len(self.holdrows) - 1
			tmprows = list(self.holdrows[topOfStack])
			del tmprows[delRowNum]
			self.holdrows[topOfStack] = tuple(tmprows)
			# Now restore the properties
			self.__restoreProps()
		else:
			# Nothing was deleted
			self.BackendObject.noResultsOnDelete()
	
	
	def flush(self):
		""" Some backends need to be prompted to flush changes
		to disk even without starting a transaction. This is the method
		to call to accomplish this.
		"""
		self.BackendObject.flush(self)


	def setDefaults(self, vals):
		""" Set the default field values for newly added records.

		The 'vals' parameter is a dictionary of fields and their default values.
		The memento must be updated afterwards, since these should not count
		as changes to the original values. 
		"""
		row = self._records[self.RowNumber]
		for kk, vv in vals.items():
			row[kk] = vv
		row[k.CURSOR_MEMENTO].setMemento(row)


	def addMemento(self, rownum=-1):
		""" Add a memento to the specified row. If the rownum is -1, 
		a memento will be added to all rows. 
		"""
		if rownum == -1:
			# Make sure that there are rows to process
			if self.RowCount < 1:
				return
			for i in range(0, self.RowCount):
				self.addMemento(i)
		row = self._records[rownum]
		if not row.has_key(k.CURSOR_MEMENTO):
			row[k.CURSOR_MEMENTO] = dMemento()
		# Take the snapshot of the current values
		row[k.CURSOR_MEMENTO].setMemento(row)


	def __setStructure(self):
		""" Try using the no-records version of the SQL statement. Otherwise,
		we need to parse the sql property to get what we need.
		"""
		try:
			tmpsql = self.getStructureOnlySql()
		except AttributeError:
			import re
			pat = re.compile("(\s*select\s*.*\s*from\s*.*\s*)((?:where\s(.*))+)\s*", re.I | re.M)
			if pat.search(self.sql):
				# There is a WHERE clause. Add the NODATA clause
				tmpsql = pat.sub("\\1 where 1=0 ", self.sql)
			else:
				# no WHERE clause. See if it has GROUP BY or ORDER BY clauses
				pat = re.compile("(\s*select\s*.*\s*from\s*.*\s*)((?:group\s*by\s(.*))+)\s*", re.I | re.M)
				if pat.search(self.sql):
					tmpsql = pat.sub("\\1 where 1=0 ", self.sql)
				else:               
					pat = re.compile("(\s*select\s*.*\s*from\s*.*\s*)((?:order\s*by\s(.*))+)\s*", re.I | re.M)
					if pat.search(self.sql):
						tmpsql = pat.sub("\\1 where 1=0 ", self.sql)
					else:               
						# Nothing. So just tack it on the end.
						tmpsql = self.sql + " where 1=0 "

		# If we already have row information, we need to save
		# and restore the cursor properties, since this query will wipe 'em out.
		if hasattr(self, "_records"):
			self.__saveProps()
			self.execute(tmpsql)
			self.__restoreProps()
		else:
			# Just run the blank query
			self.execute(tmpsql)

		dscrp = self.description
		for fld in dscrp:
			fldname = fld[0]

			### For now, just initialize the fields to empty strings,
			###    and let the updates take care of the type.
			self._blank[fldname] = ""
		# Mark the calculated and derived fields.
		self.__setNonUpdateFields()


	def moveToPK(self, pk):
		""" Find the record with the passed primary key, and make it active.

		If the record is not found, the position is set to the first record. 
		"""
		self.RowNumber = 0
		for i in range(0, len(self._records)):
			rec = self._records[i]
			if rec[self.KeyField] == pk:
				self.RowNumber = i
				break


	def moveToRowNum(self, rownum):
		""" Move the record pointer to the specified row number.

		If the specified row does not exist, the pointer remains where it is, 
		and an exception is raised.
		"""
		if (rownum >= self.RowCount) or (rownum < 0):
			raise dException.dException, _("Invalid row specified.")
		self.RowNumber = rownum


	def seek(self, val, fld=None, caseSensitive=True, near=False):
		""" Find the first row where the field value matches the passed value.

		Returns the row number of the first record that matches the passed
		value in the designated field, or -1 if there is no match. If 'near' is
		True, a match will happen on the row whose value is the greatest value
		that is less than the passed value. If 'caseSensitive' is set to False,
		string comparisons are done in a case-insensitive fashion.
		"""
		ret = -1
		if fld is None:
			# Default to the current sort order field
			fld = self.sortColumn
		if self.RowCount <= 0:
			# Nothing to seek within
			return ret
		# Make sure that this is a valid field
		if not fld:
			raise dException.dException, _("No field specified for seek()")
		if not fld or not self._records[0].has_key(fld):
			raise dException.dException, _("Non-existent field")

		# Copy the specified field vals and their row numbers to a list, and 
		# add those lists to the sort list
		sortList = []
		for i in range(0, self.RowCount):
			sortList.append( [self._records[i][fld], i] )

		# Determine if we are seeking string values
		compString = type(sortList[0][0]) in (types.StringType, types.UnicodeType)

		if not compString:
			# coerce val to be the same type as the field type
			if type(sortList[0][0]) == type(int()):
				try:
					val = int(val)
				except ValueError:
					val = int(0)

			elif type(sortList[0][0]) == type(long()):
				try:
					val = long(val)
				except ValueError:
					val = long(0)

			elif type(sortList[0][0]) == type(float()):
				try:
					val = float(val)
				except ValueError:
					val = float(0)

		if compString and not caseSensitive:
			# Use a case-insensitive sort.
			sortList.sort(lambda x, y: cmp(x[0].lower(), y[0].lower()))
		else:
			sortList.sort()

		# Now iterate through the list to find the matching value. I know that 
		# there are more efficient search algorithms, but for this purpose, we'll
		# just use brute force
		for fldval, row in sortList:
			if not compString or caseSensitive:
				match = (fldval == val)
			else:
				# Case-insensitive string search.
				match = (fldval.lower() == val.lower())

			if match:
				ret = row
				break
			else:
				if near:
					ret = row
				# If we are doing a near search, see if the row is less than the
				# requested matching value. If so, update the value of 'ret'. If not,
				# we have passed the matching value, so there's no point in 
				# continuing the search, but we mu
				if compString and not caseSensitive:
					toofar = fldval.lower() > val.lower()
				else:
					toofar = fldval > val
				if toofar:
					break
		return ret


	def checkPK(self):
		""" Verify that the field(s) specified in the KeyField prop exist.
		"""
		# First, make sure that there is *something* in the field
		if not self.KeyField:
			raise dException.dException, _("checkPK failed; no primary key specified")

		aFields = self.KeyField.split(",")
		# Make sure that there is a field with that name in the data set
		try:
			for fld in aFields:
				self._records[0][fld]
		except:
			raise dException.dException, _("Primary key field does not exist in the data set: ") + fld


	def makePkWhere(self, rec=None):
		""" Create the WHERE clause used for updates, based on the pk field. 

		Optionally pass in a record object, otherwise use the current record.
		"""
		tblPrefix = self.Table + "."
		if not rec:
			rec = self._records[self.RowNumber]
		aFields = self.KeyField.split(",")
		ret = ""
		for fld in aFields:
			if ret:
				ret += " AND "
			pkVal = rec[fld]
			if type(pkVal) in (types.StringType, types.UnicodeType):
				ret += tblPrefix + fld + "='" + pkVal.encode(self.__encoding) + "' "  
			else:
				ret += tblPrefix + fld + "=" + str(pkVal) + " "
		return ret


	def makeUpdClause(self, diff):
		""" Create the 'set field=val' section of the Update statement. 
		"""
		ret = ""
		tblPrefix = self.Table + "."
		
		for fld, val in diff.items():
			# Skip the fields that are not to be updated.
			if fld in self.getNonUpdateFields():
				continue
			if ret:
				ret += ", "
			
			if type(val) in (types.StringType, types.UnicodeType):
				escVal = self.escQuote(val)
				ret += tblPrefix + fld + " = " + escVal + " "
			else:
				if type(val) == type(datetime.date(1,1,1)):
					ret += tblPrefix + fld + " = " + self.formatDateTime(val)
				else:
					ret += tblPrefix + fld + " = " + str(val) + " "
		return ret


	def __saveProps(self, saverows=True):
		""" Push the current state of the cursor onto the stack """
		if hasattr(self, "_records"):
			self.holdrows.append(self._records)
			self.holdcount.append(self.RowCount)
			self.holdpos.append(self.RowNumber)
			self.holddesc.append(self.description)
		else:
			# Cursor hasn't been populated yet
			self.holdrows.append(None)
			self.holdcount.append(self.RowCount)
			self.holdpos.append(0)
			self.holddesc.append( () )


	def __restoreProps(self, restoreRows=True):
		""" Restore the cursor to the state of the top of the 
		stack, and then pop those values off of the stack.
		"""
		stackPos = len(self.holdrows) -1
		if restoreRows:
			self._records = self.holdrows[stackPos]
		self.RowNumber = min(self.holdpos[stackPos], self.RowCount-1)
		self.description = self.holddesc[stackPos]
		# Pop the top values off of the stack
		del self.holdrows[stackPos]
		del self.holdcount[stackPos]
		del self.holdpos[stackPos]
		del self.holddesc[stackPos]		


	def processFields(self, str):
		return self.BackendObject.processFields(str)
		
	
	def escQuote(self, val):
		""" Escape special characters in SQL strings. """
		ret = val
		if type(val) in (types.StringType, types.UnicodeType):
			ret = self.BackendObject.escQuote(val)
		return ret          


	def isAdding(self):
		""" Return True if the current record is a new record.
		"""
		return self._records[self.RowNumber].has_key(k.CURSOR_NEWFLAG)
	
	def getTables(self, includeSystemTables=False):
		""" Return a tuple of tables in the current database.
		"""
		return self.BackendObject.getTables(includeSystemTables)
		
	def getTableRecordCount(self, tableName):
		""" Get the number of records in the backend table.
		"""
		return self.BackendObject.getTableRecordCount(tableName)
		
	def getFields(self, tableName):
		""" Get field information about the backend table.
		
		Returns a tuple of 3-tuples, where the outer tuple is the list
		of fields, and the 3-tuple's elements are:
			0: the field name (string)
			1: the field type ('I', 'N', 'C', 'M', 'B', 'D', 'T')
			2: boolean specifying whether this is a pk field.
		"""
		return self.BackendObject.getFields(tableName)
		
	def getLastInsertID(self):
		""" Return the most recently generated PK """
		ret = None
		if self.BackendObject:
			self.__saveProps()
			ret = self.BackendObject.getLastInsertID(self)
			self.__restoreProps()
		return ret

	
	def formatDateTime(self, val):
		""" Format DateTime values for the backend """
		ret = val
		if self.BackendObject:
			ret = self.BackendObject.formatDateTime(val)
		return ret


	def beginTransaction(self):
		""" Begin a SQL transaction."""
		ret = None
		if self.BackendObject:
			self.__saveProps()
			ret = self.BackendObject.beginTransaction(self)
			self.__restoreProps()
		return ret


	def commitTransaction(self):
		""" Commit a SQL transaction."""
		ret = None
		if self.BackendObject:
			self.__saveProps()
			ret = self.BackendObject.commitTransaction(self)
			self.__restoreProps()
		return ret


	def rollbackTransaction(self):
		""" Roll back (revert) a SQL transaction."""
		ret = None
		if self.BackendObject:
			self.__saveProps()
			ret = self.BackendObject.rollbackTransaction(self)
			self.__restoreProps()
		return ret
	

	###     SQL Builder methods     ########
	def getFieldClause(self):
		""" Get the field clause of the sql statement.
		"""
		return self._fieldClause

	def setFieldClause(self, clause):
		""" Set the field clause of the sql statement.
		"""
		self._fieldClause = clause

	def addField(self, exp):
		""" Add a field to the field clause.
		"""
		if self.BackendObject:
			self._fieldClause = self.BackendObject.addField(self._fieldClause, exp)

	def getFromClause(self):
		""" Get the from clause of the sql statement.
		"""
		return self._fromClause

	def setFromClause(self, clause):
		""" Set the from clause of the sql statement.
		"""
		self._fromClause = clause

	def addFrom(self, exp):
		""" Add a table to the sql statement.

		For joins, use setFromClause() to set the entire from clause
		explicitly.
		"""
		if self.BackendObject:
			self._fromClause = self.BackendObject.addFrom(self._fromClause, exp)

	def getWhereClause(self):
		""" Get the where clause of the sql statement.
		"""
		return self._whereClause

	def setWhereClause(self, clause):
		""" Set the where clause of the sql statement.
		"""
		self._whereClause = clause

	def addWhere(self, exp, comp="and"):
		""" Add an expression to the where clause.
		"""
		if self.BackendObject:
			self._whereClause = self.BackendObject.addWhere(self._whereClause, exp, comp)

	def prepareWhere(self, clause):
		""" Modifies WHERE clauses as needed for each backend. """
		return self.BackendObject.prepareWhere(clause)
		
	def getChildFilterClause(self):
		""" Get the child filter part of the sql statement.
		"""
		return self._childFilterClause

	def setChildFilterClause(self, clause):
		""" Set the child filter clause of the sql statement.
		"""
		self._childFilterClause = clause

	def getGroupByClause(self):
		""" Get the group-by clause of the sql statement.
		"""
		return self._groupByClause

	def setGroupByClause(self, clause):
		""" Set the group-by clause of the sql statement.
		"""
		self._groupByClause = clause

	def addGroupBy(self, exp):
		""" Add an expression to the group-by clause.
		"""
		if self.BackendObject:
			self._groupByClause = self.BackendObject.addGroupBy(self._groupByClause, exp)

	def getOrderByClause(self):
		""" Get the order-by clause of the sql statement.
		"""
		return self._orderByClause

	def setOrderByClause(self, clause):
		""" Set the order-by clause of the sql statement.
		"""
		self._orderByClause = clause

	def addOrderBy(self, exp):
		""" Add an expression to the order-by clause.
		"""
		if self.BackendObject:
			self._orderByClause = self.BackendObject.addOrderBy(self._orderByClause, exp)

	def getLimitClause(self):
		""" Get the limit clause of the sql statement.
		"""
		return self._limitClause

	def setLimitClause(self, clause):
		""" Set the limit clause of the sql statement.
		"""
		self._limitClause = clause

	def getLimitWord(self):
		""" Return the word to use in the db-specific limit clause.
		"""
		ret = "limit"
		if self.BackendObject:
			ret = self.BackendObject.getLimitWord()
		return ret
			
	def getLimitPosition(self):
		""" Return the position to place the limit clause.
		
		For currently-supported dbapi's, the return values of 'top' or 'bottom'
		are sufficient.
		"""
		ret = "bottom"
		if self.BackendObject:
			ret = self.BackendObject.getLimitPosition()
		return ret			
			
	def getSQL(self):
		""" Get the complete SQL statement from all the parts.
		"""
		fieldClause = self._fieldClause
		fromClause = self._fromClause
		whereClause = self._whereClause
		childFilterClause = self._childFilterClause
		groupByClause = self._groupByClause
		orderByClause = self._orderByClause
		limitClause = self._limitClause

		if not fieldClause:
			fieldClause = "*"
		
		if childFilterClause:
			# Prepend it to the where clause
			if whereClause:
				childFilterClause += "\nand "
			whereClause = childFilterClause + " " + whereClause

		if fromClause: 
			fromClause = "from " + fromClause
		else:
			fromClause = "from " + self.Table
		if whereClause:
			whereClause = "where " + whereClause
		if groupByClause:
			groupByClause = "group by " + groupByClause
		if orderByClause:
			orderByClause = "order by " + orderByClause
		if limitClause:
			limitClause = self.getLimitWord() + " " + limitClause
		else:
			limitClause = self.getLimitWord() + " " + str(self._defaultLimit)

		return self.BackendObject.formSQL(fieldClause, fromClause, 
				whereClause, groupByClause, orderByClause, limitClause)
		

	def getStructureOnlySql(self):
		holdWhere = self._whereClause
		self.setWhereClause("1 = 0")
		ret = self.getSQL()
		self.setWhereClause(holdWhere)
		return ret

	def executeSQL(self, *args, **kwargs):
		self.execute(self.createSQL(), *args, **kwargs)
	###     end - SQL Builder methods     ########

	


	def _getAutoPopulatePK(self):
		try:
			return self._autoPopulatePK
		except AttributeError:
			return True
			
	def _setAutoPopulatePK(self, autopop):
		self._autoPopulatePK = bool(autopop)

	def _setBackendObject(self, obj):
		self.__backend = obj
	
	def _getBackendObject(self):
		return self.__backend
	
	def _getKeyField(self):
		try:
			return self._keyField
		except AttributeError:
			return ""
			
	def _setKeyField(self, kf):
		self._keyField = str(kf)

	def _setRowNumber(self, num):
		self.__rownumber = num
	
	def _getRowNumber(self):
		try:
			return self.__rownumber
		except AttributeError:
			return -1
	
	def _getRowCount(self):
		try:
			return len(self._records)
		except AttributeError:
			return -1

	def _getTable(self):
		try:
			return self._table
		except AttributeError:
			return ""
			
	def _setTable(self, table):
		self._table = str(table)

	
	AutoPopulatePK = property(_getAutoPopulatePK, _setAutoPopulatePK, None,
			_("When inserting a new record, does the backend populate the PK field?")) 		
	
	BackendObject = property(_getBackendObject, _setBackendObject, None,
			_("Reference to the object that handles backend-specific actions."))
	
	KeyField = property(_getKeyField, _setKeyField, None,
			_("Name of field that is the PK. If multiple fields make up the key, "
			"separate the fields with commas. (str)"))
	
	RowNumber = property(_getRowNumber, _setRowNumber, None,
			_("Current row in the recordset."))
	
	RowCount = property(_getRowCount, None, None,
			_("Current number of rows in the recordset. Read-only."))

	Table = property(_getTable, _setTable, None,
			_("The name of the table in the database that this cursor is updating."))
			
