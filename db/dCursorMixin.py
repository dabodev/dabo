import dabo.dConstants as k
from dabo.db.dMemento import dMemento
from dabo.dLocalize import _
import dabo.dException as dException
import types, datetime

class dCursorMixin:
	# Name of the primary key field for this cursor. If the PK is a composite
	# (i.e., more than one field) include both separated by a comma
	keyField = ""
	# Name of the table in the database that this cursor is getting data from
	table = ""
	# When inserting a new record, do we let the backend database populate
	# the PK field? 
	autoPopulatePK = True
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
	# Counter for the saved property stack. Prevents multiple calls
	# to __saveProps from overwriting each other.
	__propSaveStack = 0


	def __init__(self, sql="", *args, **kwargs):
		if sql:
			self.sql = sql
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


	def setSQL(self, sql):
		self.sql = sql


	def setTable(self, table):
		self.table = table


	def setKeyField(self, kf):
		self.keyField = kf


	def getSortColumn(self):
		return self.sortColumn


	def getSortOrder(self):
		return self.sortOrder


	def getSortCase(self):
		return self.sortCase


	def setAutoPopulatePK(self, autopop):
		self.autoPopulatePK = autopop


	def execute(self, sql, params=None):
		"""
		The idea here is to let the super class do the actual work in retrieving the data. However, 
		many cursor classes can only return row information as a list, not as a dictionary. This
		method will detect that, and convert the results to a dictionary.
		"""
		res = self.superCursor.execute(self, sql, params)

		if self._rows:
			if type(self._rows[0]) == types.TupleType:
				# Need to convert each row to a Dict
				tmpRows = []
				# First, get the description property and extract the field names from that
				fldNames = []
				for fld in self.description:
					fldNames.append(fld[0])
				fldcount = len(fldNames)
				# Now go through each row, and convert it to a dictionary. We will then
				# add that dictionary to the tmpRows list. When all is done, we will replace 
				# the _rows property with that list of dictionaries
				for row in self._rows:
					dic= {}
					for i in range(0, fldcount):
						dic[fldNames[i]] = row[i]
					tmpRows.append(dic)
				self._rows = tuple(tmpRows)
		return res
	
	
	def requery(self, params=None):
		self.lastSQL = self.sql
		self.lastParams = params
		
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
		if self.rowcount < 1:
			raise dException.NoRecordsException, _("No rows to sort.")

		# Make sure that the specified column is a column in the result set
		if not self._rows[0].has_key(col):
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
			for row in self._rows:
				self.__unsortedRows.append(row[self.keyField])

		# First, preserve the PK of the current row so that we can reset
		# the rownumber property to point to the same row in the new order.
		currRowKey = self._rows[self.rownumber][self.keyField]
		# Create the list to hold the rows for sorting
		sortList = []
		if not ord:
			# Restore the rows to their unsorted order
			for row in self._rows:
				sortList.append([self.__unsortedRows.index(row[self.keyField]), row])
		else:
			for row in self._rows:
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
		# Extract the rows into a new list, then convert them back to the _rows tuple
		newRows = []
		for elem in sortList:
			newRows.append(elem[1])
		self._rows = tuple(newRows)

		# restore the rownumber
		for i in range(0, self.rowcount):
			if self._rows[i][self.keyField] == currRowKey:
				self.rownumber = i
				break


	def setNonUpdateFields(self, fldList=[]):
		self.nonUpdateFields = fldList
	
	
	def getNonUpdateFields(self):
		return self.nonUpdateFields + self.__nonUpdateFields
		
		
	def __setNonUpdateFields(self):
		# Set the __nonUpdateFields prop
		self.__nonUpdateFields = []
		
		dscrp = self.description
		self.__saveProps()
		for fldDesc in dscrp:
			fld = fldDesc[0]
			try:
				sql = """select %s from %s limit 1""" % (fld, self.table)
				self.execute( sql )
				# Get the description for this single field
				dsc = self.description[0]
				# All members except for the second (display value) should 
				# match. If not, add 'em to the nonUpdateFields list
				if not ( (fldDesc[1] == dsc[1]) 
						and (fldDesc[3] == dsc[3]) and (fldDesc[4] == dsc[4]) 
						and (fldDesc[5] == dsc[5]) and (fldDesc[6] == dsc[6]) ):
					self.__nonUpdateFields.append(fld)
			except:
				self.__nonUpdateFields.append(fld)
	
		self.__restoreProps()
	

	def isChanged(self, allRows=True):
		""" 	Scan all the records and compare them with their mementos. 
		Returns True if any differ, False otherwise.
		"""
		ret = False

		if self.rowcount > 0:
			if allRows:
				recs = self._rows
			else:
				recs = (self._rows[self.rownumber],)

			for i in range(len(recs)):
				rec = recs[i]
				if self.isRowChanged(rec):
					ret = True
					break
		return ret


	def isRowChanged(self, rec):
		mem = rec[k.CURSOR_MEMENTO]
		newrec = rec.has_key(k.CURSOR_NEWFLAG)
		ret = newrec or mem.isChanged(rec)
		return ret


	def setMemento(self):
		if self.rowcount > 0:
			if (self.rownumber >= 0) and (self.rownumber < self.rowcount):
				self.addMemento(self.rownumber)
	
	
	def genTempAutoPK(self):
		""" Create a temporary PK for a new record. Set the key field to this
		value, and also create a temp field to hold it so that when saving the
		new record, child records that are linked to this one can be updated
		with the actual PK value.
		"""
		rec = self._rows[self.rownumber]
		tmpPK = self._genTempPKVal()
		rec[self.keyField] = tmpPK
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
		if self.rowcount <= 0:
			raise dException.NoRecordsException, _("No records in the data set.")
		rec = self._rows[self.rownumber]
		if rec.has_key(k.CURSOR_NEWFLAG):
			# New, unsaved record
			return rec[k.CURSOR_TMPKEY_FIELD]


	def getFieldVal(self, fld):
		""" Return the value of the specified field.
		"""
		ret = None
		if self.rowcount <= 0:
			raise dException.NoRecordsException, _("No records in the data set.")

		rec = self._rows[self.rownumber]
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
		if self.rowcount <= 0:
			raise dException.dException, _("No records in the data set")
		else:
			rec = self._rows[self.rownumber]
			if rec.has_key(fld):
				if type(rec[fld]) != type(val):
					if ( type(val) in (types.UnicodeType, types.StringType) 
							and type(rec[fld]) is types.StringType ):
						val = str(val)
				if type(rec[fld]) != type(val):
					# This can happen with a new record, since we just stuff the
					# fields full of empty strings.
					if not self._rows[self.rownumber].has_key(k.CURSOR_NEWFLAG):
						print "!!! Data Type Mismatch:", type(rec[fld]), type(val)
					
					if type(rec[fld]) == type(int()) and type(val) == type(bool()):
						# convert bool to int (original field val was int, but UI
						# changed to int. 
						val = int(val)
						
				rec[fld] = val
			else:
				raise dException.dException, "%s '%s' %s" % (
							_("Field"),
							fld,
							_("does not exist in the data set")
							)


	def getRecordStatus(self, rownum=None):
		""" Returns a dictionary containing an element for each changed 
		field in the specified record (or the current record if none is specified).
		The field name is the key for each element; the value is a 2-element
		tuple, with the first element being the original value, and the second 
		being the current value.
		"""
		if rownum is None:
			rownum = self.rownumber
		try:
			row = self._rows[rownumber]
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
			return self._rows
		except AttributeError:
			return ()


	def getRowCount(self):
		""" Get the row count of the current data set.
		"""
		try:
			return self.rowcount
		except AttributeError:
			return -1


	def getRowNumber(self):
		""" Get the active row number of the data set.
		"""
		try:
			return self.rownumber
		except AttributeError:
			return -1


	def first(self):
		""" Move the record pointer to the first record of the data set. 
		"""
		if self.rowcount > 0:
			self.rownumber = 0
		else:
			raise dException.NoRecordsException, _("No records in data set")


	def prior(self):
		""" Move the record pointer back one position in the recordset.
		"""
		if self.rowcount > 0:
			if self.rownumber > 0:
				self.rownumber -= 1
			else:
				raise dException.BeginningOfFileException, _("Already at the beginning of the data set.")
		else:
			raise dException.NoRecordsException, _("No records in data set")


	def next(self):
		""" Move the record pointer forward one position in the recordset.
		"""
		if self.rowcount > 0:
			if self.rownumber < (self.rowcount-1):
				self.rownumber += 1
			else:
				raise dException.EndOfFileException, _("Already at the end of the data set.")
		else:
			raise dException.NoRecordsException, _("No records in data set")


	def last(self):
		""" Move the record pointer to the last record in the recordset.
		"""
		if self.rowcount > 0:
			self.rownumber = self.rowcount-1
		else:
			raise dException.NoRecordsException, _("No records in data set")


	def save(self, allrows=False):
		""" Save any changes to the data back to the data store.
		"""
		# Make sure that there is data to save
		if self.rowcount <= 0:
			raise dException.dException, _("No data to save")

		# Make sure that there is a PK
		self.checkPK()

		if allrows:
			recs = self._rows
		else:
			recs = (self._rows[self.rownumber],)

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
					if self.autoPopulatePK and (kk == self.keyField):
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
						vals += ", " + str(self.__escQuote(vv))
				# Trim leading comma-space from the strings
				flds = flds[2:]
				vals = vals[2:]
				sql = "insert into %s (%s) values (%s) " % (self.table, flds, vals)

			else:
				pkWhere = self.makePkWhere(rec)
				updClause = self.makeUpdClause(diff)
				sql = "update %s set %s where %s" % (self.table, updClause, pkWhere)

			# Save off the props that will change on the update
			self.__saveProps()
			#run the update
			res = self.execute(sql)

			if newrec and self.autoPopulatePK:
				# Call the database backend-specific code to retrieve the
				# most recently generated PK value.
				newPKVal = self.getLastInsertID()
			# restore the orginal values
			self.__restoreProps()

			if newrec and self.autoPopulatePK:
				self.setFieldVal(self.keyField, newPKVal)

			if newrec:
				# Need to remove the new flag
				del rec[k.CURSOR_NEWFLAG]
			else:
				if not res:
					raise dException.dException, _("No records updated")

	
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
		# Copy the _blank dict to the _rows, and adjust everything accordingly
		tmprows = list(self._rows)
		tmprows.append(self._blank.copy())
		self._rows = tuple(tmprows)
		# Adjust the rowcount and position
		self.rowcount = len(self._rows)
		self.rownumber = self.rowcount - 1
		# Add the 'new record' flag to the last record (the one we just added)
		self._rows[self.rownumber][k.CURSOR_NEWFLAG] = True
		# Add the memento
		self.addMemento(self.rownumber)


	def cancel(self, allrows=False):
		""" Revert any changes to the data set back to the original values.
		"""
		# Make sure that there is data to save
		if not self.rowcount > 0:
			raise dException.dException, _("No data to cancel")

		if allrows:
			recs = self._rows
		else:
			recs = (self._rows[self.rownumber],)

		# Create a list of PKs for each 'eligible' row to cancel
		cancelPKs = []
		for rec in recs:
			cancelPKs.append(rec[self.keyField])

		for i in range(self.rowcount-1, -1, -1):
			rec = self._rows[i]

			if rec[self.keyField] in cancelPKs:
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
		if not hasattr(self, "rownumber"):
			# No query has been run yet
			raise dException.NoRecordsException, _("No record to delete")
		if delRowNum is None:
			# assume that it is the current row that is to be deleted
			delRowNum = self.rownumber

		rec = self._rows[delRowNum]
		newrec =  rec.has_key(k.CURSOR_NEWFLAG)
		self.__saveProps(saverows=False)
		if newrec:
			tmprows = list(self._rows)
			del tmprows[delRowNum]
			self._rows = tuple(tmprows)
			res = True
		else:
			pkWhere = self.makePkWhere()
			sql = "delete from %s where %s" % (self.table, pkWhere)
			res = self.execute(sql)

		if res:
			# First, delete the row from the held properties
			tmprows = list(self.holdrows)
			del tmprows[delRowNum]
			self.holdrows = tuple(tmprows)
			# Now restore the properties
			self.__restoreProps()
		else:
			# Nothing was deleted
			raise dException.dException, _("No records deleted")


	def setDefaults(self, vals):
		""" Set the default field values for newly added records.

		The 'vals' parameter is a dictionary of fields and their default values.
		The memento must be updated afterwards, since these should not count
		as changes to the original values. 
		"""
		row = self._rows[self.rownumber]
		for kk, vv in vals.items():
			row[kk] = vv
		row[k.CURSOR_MEMENTO].setMemento(row)


	def addMemento(self, rownum=-1):
		""" Add a memento to the specified row. If the rownum is -1, 
		a memento will be added to all rows. 
		"""
		if rownum == -1:
			# Make sure that there are rows to process
			if self.rowcount < 1:
				return
			for i in range(0, self.rowcount):
				self.addMemento(i)
		row = self._rows[rownum]
		if not row.has_key(k.CURSOR_MEMENTO):
			row[k.CURSOR_MEMENTO] = dMemento()
		# Take the snapshot of the current values
		row[k.CURSOR_MEMENTO].setMemento(row)


	def __setStructure(self):
		""" If this instance was created with the SqlBuilderMixin, we can just 
		use that to get the no-records version of the SQL statement. Otherwise,
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
		if hasattr(self, "_rows"):
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
		self.rownumber = 0
		for i in range(0, len(self._rows)):
			rec = self._rows[i]
			if rec[self.keyField] == pk:
				self.rownumber = i
				break


	def moveToRowNum(self, rownum):
		""" Move the record pointer to the specified row number.

		If the specified row does not exist, the pointer remains where it is, 
		and an exception is raised.
		"""
		if (rownum >= self.rowcount) or (rownum < 0):
			raise dException.dException, _("Invalid row specified.")
		self.rownumber = rownum


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
		if self.rowcount <= 0:
			# Nothing to seek within
			return ret
		# Make sure that this is a valid field
		if not fld:
			raise dException.dException, _("No field specified for seek()")
		if not fld or not self._rows[0].has_key(fld):
			raise dException.dException, _("Non-existent field")

		# Copy the specified field vals and their row numbers to a list, and 
		# add those lists to the sort list
		sortList = []
		for i in range(0, self.rowcount):
			sortList.append( [self._rows[i][fld], i] )

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
		""" Verify that the field(s) specified in the keyField prop exist.
		"""
		# First, make sure that there is *something* in the field
		if not self.keyField:
			raise dException.dException, _("checkPK failed; no primary key specified")

		aFields = self.keyField.split(",")
		# Make sure that there is a field with that name in the data set
		try:
			for fld in aFields:
				self._rows[0][fld]
		except:
			raise dException.dException, _("Primary key field does not exist in the data set: ") + fld


	def makePkWhere(self, rec=None):
		""" Create the WHERE clause used for updates, based on the pk field. 

		Optionally pass in a record object, otherwise use the current record.
		"""
		if not rec:
			rec = self._rows[self.rownumber]
		aFields = self.keyField.split(",")
		ret = ""
		for fld in aFields:
			if ret:
				ret += " AND "
			pkVal = rec[fld]
			if type(pkVal) == types.StringType:
				ret += fld + "='" + pkVal + "' "  
			else:
				ret += fld + "=" + str(pkVal) + " "
		return ret


	def makeUpdClause(self, diff):
		""" Create the 'set field=val' section of the Update statement. 
		"""
		ret = ""
		for fld, val in diff.items():
			# Skip the fields that are not to be updated.
			if fld in self.getNonUpdateFields():
				continue
			if ret:
				ret += ", "
			
			if type(val) in (types.StringType, types.UnicodeType):
				ret += fld + " = " + self.__escQuote(val) + " "
			else:
				if type(val) == type(datetime.date(1,1,1)):
					ret += fld + " = " + self.formatDateTime(val)
				else:
					ret += fld + " = " + str(val) + " "
		return ret


	def __saveProps(self, saverows=True):
		""" Push the current state of the cursor onto the stack """
		if hasattr(self, "_rows"):
			self.holdrows.append(self._rows)
			self.holdcount.append(self.rowcount)
			self.holdpos.append(self.rownumber)
			self.holddesc.append(self.description)
		else:
			# Cursor hasn't been populated yet
			self.holdrows.append(None)
			self.holdcount.append(self.rowcount)
			self.holdpos.append(0)
			self.holddesc.append( () )


	def __restoreProps(self, restoreRows=True):
		""" Restore the cursor to the state of the top of the 
		stack, and then pop those values off of the stack.
		"""
		stackPos = len(self.holdrows) -1
		if restoreRows:
			self._rows = self.holdrows[stackPos]
		if self._rows:
			self.rowcount = len(self._rows)
		else:
			self.rowcount = self.holdcount[stackPos]
		self.rownumber = min(self.holdpos[stackPos], self.rowcount-1)
		self.description = self.holddesc[stackPos]
		# Pop the top values off of the stack
		del self.holdrows[stackPos]
		del self.holdcount[stackPos]
		del self.holdpos[stackPos]
		del self.holddesc[stackPos]		


	def __escQuote(self, val):
		""" Escape special characters in SQL strings.

		Escapes any single quotes that could cause SQL syntax errors. Also 
		escapes backslashes, since they have special meaning in SQL parsing. 
		Finally, wraps the value in single quotes.
		"""
		ret = val
		if type(val) in (types.StringType, types.UnicodeType):
			# escape and then wrap in single quotes
			sl = "\\"
			qt = "\'"
			ret = qt + val.replace(sl, sl+sl).replace(qt, sl+qt) + qt
		return ret          


	def isAdding(self):
		""" Return True if the current record is a new record.
		"""
		return self._rows[self.rownumber].has_key(k.CURSOR_NEWFLAG)


	def beginTransaction(self):
		""" Begin a SQL transaction.

		Override in subclasses.
		"""
		pass


	def commitTransaction(self):
		""" Commit a SQL transaction.

		Override in subclasses.
		"""
		pass


	def rollbackTransaction(self):
		""" Roll back (revert) a SQL transaction.

		Override in subclasses.
		"""
		pass
