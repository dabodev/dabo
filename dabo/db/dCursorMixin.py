import types, datetime, inspect, sys, re

import dabo
import dabo.dConstants as k
from dabo.db.dMemento import dMemento
from dabo.dLocalize import _
import dabo.dException as dException
import dabo.common

class dCursorMixin(dabo.common.dObject):
	def __init__(self, sql="", *args, **kwargs):
		self.initProperties()
		if sql and isinstance(sql, basestring) and len(sql) > 0:
			self.UserSQL = sql

		#dCursorMixin.doDefault()
		#super(dCursorMixin, self).__init__()
		## pkm: Neither of the above are correct. We need to explicitly
		##      call dObject's __init__, otherwise the cursor object with
		##      which we are mixed-in will take the __init__.
		dabo.common.dObject.__init__(self)
		
		# Just in case this is used outside of the context of a bizobj
		if not hasattr(self, "superCursor") or self.superCursor is None:
			myBases = self.__class__.__bases__
			for base in myBases:
				# Find the first base class that doesn't have the 'autoPopulatePK'
				# attribute. Designate that class as the superCursor class.
				if hasattr(base, "fetchall"):
					self.superCursor = base
					break


	def initProperties(self):
		# Holds the dict used for adding new blank records
		self._blank = {}
		# Last executed sql params
		self.lastParams = None
		# Column on which the result set is sorted
		self.sortColumn = ""
		# Order of the sorting. Should be either ASC, DESC or empty for no sort
		self.sortOrder = ""
		# Is the sort case-sensitive?
		self.sortCase = True
		# Holds the keys in the original, unsorted order for unsorting the dataset
		self.__unsortedRows = []
		# Holds the name of fields to be skipped when updating the backend, such
		# as calculated or derived fields, or fields that are otherwise not to be updated.
		self.__nonUpdateFields = []
		# User-editable list of non-updated fields
		self.nonUpdateFields = []
		# Flag that is set when the user explicitly sets the Key Field
		self._keyFieldSet = False
		# Cursor that manages this cursor's SQL. Default to self; 
		# in some cases, such as a single bizobj managing several cursors, 
		# it will be a separate object.
		self.sqlManager = self
		# Attribute that holds the data of the cursor
		self._records = ()
		# Attribute that holds the current row number
		self.__rownumber = -1

		self._blank = {}
		self.__unsortedRows = []
		self.nonUpdateFields = []
		self.__tmpPK = -1		# temp PK value for new records.
		# Holds the data types for each field
		self._types = {}
		
		# Holds reference to auxiliary cursor that handles queries that
		# are not supposed to affect the record set.
		self.__auxCursor = None

		# Reference to the object with backend-specific behaviors
		self.__backend = None
		
		# set properties for the SQL Builder functions
		self.clearSQL()
		self.hasSqlBuilder = True
		
		# props for building the auxiliary cursor
		self._cursorFactoryFunc = None
		self._cursorFactoryClass = None


	def setCursorFactory(self, func, cls):
		self._cursorFactoryFunc = func
		self._cursorFactoryClass = cls
		
	
	def setSQL(self, sql):
		pass
		# This function isn't needed anymore
		#self.sql = self._getBackendObject().setSQL(sql)


	def clearSQL(self):
		self._fieldClause = ""
		self._fromClause = ""
		self._whereClause = ""
		self._childFilterClause = ""
		self._groupByClause = ""
		self._orderByClause = ""
		self._limitClause = ""
		self._defaultLimit = 1000

		
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
		if isinstance(sql, unicode):
			sqlEX = sql.encode(self.Encoding)
		else:
			sqlEX = sql
		
		try:
			if params is None or len(params) == 0:
				res = self.superCursor.execute(self, sqlEX)
			else:
				res = self.superCursor.execute(self, sqlEX, params)
		except Exception, e:
			raise dException.dException, e
		# Not all backends support 'fetchall' after executing a query
		# that doesn't return records, such as an update.
		try:
			self._records = self.fetchall()
		except:
			pass
		
		# Some backend programs do odd things to the description
		# This allows each backend to handle these quirks individually.
		self._getBackendObject().massageDescription(self)
		
		if self.RowCount > 0:
			self.RowNumber = max(0, self.RowNumber)
			maxrow = max(0, (self.RowCount-1) )
			self.RowNumber = min(self.RowNumber, maxrow)

		if self._records:
			if isinstance(self._records[0], tuple) or isinstance(self._records[0], list):
				# Need to convert each row to a Dict
				tmpRows = []
				# First, get the description property and extract the field names from that
				fldNames = []
				for fld in self.FieldDescription:
					fldNames.append(fld[0].lower())
				fldcount = len(fldNames)
				# Now go through each row, and convert it to a dictionary. We will then
				# add that dictionary to the tmpRows list. When all is done, we will replace 
				# the _records property with that list of dictionaries
				for row in self._records:
					dic= {}
					for i in range(0, fldcount):
						if isinstance(row[i], str):
							# String; convert it to unicode
							dic[fldNames[i]] = unicode(row[i], self.Encoding)
						else:
							dic[fldNames[i]] = row[i]
					tmpRows.append(dic)
				self._records = tuple(tmpRows)

			else:
				# Make all string values into unicode
				for row in self._records:
					for fld in row.keys():
						val = row[fld]
						if isinstance(val, str):	
							# String; convert it to unicode
							row[fld]= unicode(val, self.Encoding)
			
			# There can be a problem with the MySQLdb adapter if
			# the mx modules are installed on the machine, the adapter
			# will use that type instead of the native datetime.
			try:
				import mx.DateTime
				mxdt = mx.DateTime.DateTimeType
				for row in self._records:
					for fld in row.keys():
						val = row[fld]
						if isinstance(val, mxdt):
							# Convert to normal datetime
							row[fld]= datetime.datetime(val.year, val.month, val.day, 
									val.hour, val.minute, int(val.second) )
			except ImportError:
				# mx not installed; no problem
				pass
		return res
	
	
	def requery(self, params=None):
		self._lastSQL = self.CurrentSQL
		self.lastParams = params
		
		self.execute(self.CurrentSQL, params)
		
		# Store the data types for each field
		self.storeFieldTypes()
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


	def storeFieldTypes(self):
		"""Stores the data type for each column in the result set."""
		self._types = {}
		if self.RowCount > 0:
			rec = self._records[0]
			for fname, fval in rec.items():
				self._types[fname] = type(fval)
			
		
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

		newCol = col
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
		try:
			currRowKey = self._records[self.RowNumber][self.KeyField]
		except IndexError:
			# Row no longer exists, such as after a Requery that returns
			# fewer rows.
			currRowKey = None
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
		compString = isinstance(sortList[0][0], basestring)
		sortfunc = None
		if compString and not caseSensitive:
			# Use a case-insensitive sort.
			sortfunc = lambda x, y: cmp(x[0].lower(), y[0].lower())
		else:
			# can't compare NoneType to some types: sort None lower than anything else:
			def nonesort(v,w):
				x, y = v[0], w[0]
				if x is None and y is None:
					return 0
				elif x is None and y is not None:
					return -1
				elif x is not None and y is None:
					return 1
				else:
					return cmp(x,y)
			sortfunc = nonesort	
		sortList.sort(sortfunc)
			
		# Unless DESC was specified as the sort order, we're done sorting
		if ord == "DESC":
			sortList.reverse()
		# Extract the rows into a new list, then convert them back to the _records tuple
		newRows = []
		for elem in sortList:
			newRows.append(elem[1])
		self._records = tuple(newRows)

		# restore the RowNumber
		if currRowKey:
			for i in range(0, self.RowCount):
				if self._records[i][self.KeyField] == currRowKey:
					self.RowNumber = i
					break
		else:
			self.RowNumber = 0
	
	
	def cursorToXML(self):
		""" Returns an XML string containing the information necessary to 
		re-create this cursor.
		"""
		base = """<?xml version="1.0" encoding="%s"?>
<dabocursor xmlns="http://www.dabodev.com"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://www.dabodev.com dabocursor.xsd"
xsi:noNamespaceSchemaLocation = "http://dabodev.com/schema/dabocursor.xsd">
	<cursor autopopulate="%s" keyfield="%s" table="%s">
%s
	</cursor>
</dabocursor>"""

		rowTemplate = """		<row>
%s
		</row>
"""
		
		colTemplate = """			<column name="%s" type="%s">%s</column>"""

		rowXML = ""
		for rec in self._records:
			recInfo = [ colTemplate % (k, self.getType(v), self.escape(v)) 
					for k,v in rec.items() 
					if k != "dabo-memento"]
			rowXML += rowTemplate % "\n".join(recInfo)
		return base % (self.Encoding, self.AutoPopulatePK, self.KeyField, 
				self.Table, rowXML)

	
	def getType(self, val):
		try:
			ret = re.search("type '([^']+)'", str(type(val))).groups()[0]
		except:
			ret = "-unknown-"
		return ret
	
	
	def escape(self, val):
		""" Provides the proper escaping of values in XML output """
		ret = val
		if isinstance(val, basestring):
			if ("\n" in val) or ("<" in val) or ("&" in val):
				ret = "<![CDATA[%s]]>" % val.encode(self.Encoding)
		return ret

	def setNonUpdateFields(self, fldList=[]):
		self.nonUpdateFields = fldList
	
	
	def getNonUpdateFields(self):
		return self.nonUpdateFields + self.__nonUpdateFields
		
		
	def __setNonUpdateFields(self):
		"""Delegate this to the backend object."""
		self._getBackendObject().setNonUpdateFields(self)
	

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


	def isNewUnsaved(self):
		"""Return True if the current record is new and not yet saved.
		Return False otherwise.
		"""
		try:
			ret = self._records[self.RowNumber].has_key(k.CURSOR_NEWFLAG)
		except:
			ret = False
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
		if rec.has_key(k.CURSOR_NEWFLAG) and self.AutoPopulatePK:
			# New, unsaved record
			return rec[k.CURSOR_TMPKEY_FIELD]
		else:
			return rec[self.KeyField]


	def getFieldVal(self, fld):
		""" Return the value of the specified field."""
		ret = None
		if self.RowCount <= 0:
			raise dException.NoRecordsException, _("No records in the data set.")

		rec = self._records[self.RowNumber]
		if rec.has_key(fld):
			ret = rec[fld]
		else:
			raise dException.dException, "%s '%s' %s" % (
					_("Field"), fld, _("does not exist in the data set"))
		return ret


	def setFieldVal(self, fld, val):
		""" Set the value of the specified field. """
		if self.RowCount <= 0:
			raise dException.dException, _("No records in the data set")
		else:
			rec = self._records[self.RowNumber]
			if rec.has_key(fld):
				fldType = self._types[fld]
				if fldType != type(val):
					convTypes = (str, unicode, int, float, long, complex)
					if isinstance(val, convTypes) and isinstance(rec[fld], basestring):
						if isinstance(rec[fld], str):
							val = str(val)
						else:
							val = unicode(val)
					elif isinstance(rec[fld], int) and isinstance(val, bool):
						# convert bool to int (original field val was int, but UI
						# changed to int. 
						val = int(val)
				if fldType != type(val):
					ignore = False
					# Date and DateTime types are handled as character, even if the 
					# native field type is not. Ignore these. NOTE: we have to deal with the 
					# string representation of these classes, as there is no primitive for either
					# 'DateTime' or 'Date'.
					dtStrings = ("<type 'DateTime'>", "<type 'Date'>", "<type 'datetime.datetime'>")
					if str(fldType) in dtStrings:
						if isinstance(val, basestring):
							ignore = True
					else:
						# This can also happen with a new record, since we just stuff the
						# fields full of empty strings.
						ignore = self._records[self.RowNumber].has_key(k.CURSOR_NEWFLAG)
					
					if not ignore:
						msg = "!!! Data Type Mismatch: field=%s. Expecting: %s; got: %s" \
						      % (fld, str(fldType), str(type(val)))
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


	def getDataSet(self, flds=None):
		""" Get the entire data set encapsulated in a tuple. If the optional
		'flds' parameter is given, the result set will be filtered to only 
		include the specified fields.
		"""
		try:
			ret = self._records
			if flds:
				retlist = []
				for rec in ret:
					filtRec = {}
					for fld in flds:
						filtRec[fld] = rec[fld]
					retlist.append(filtRec)
				ret = tuple(retlist)
			return ret
		except AttributeError:
			return ()


	def getRowCount(self):
		""" Get the row count of the current data set.
		
		Obsolete: Just get this from the property RowCount.
		"""
		return self.RowCount


	def getRowNumber(self):
		""" Get the active row number of the data set.
		
		Obsolete: Just get this from the property RowNumber.
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

		self.beginTransaction()

		for rec in recs:
			try:
				self.__saverow(rec)
			except Exception, e:
				# Error was raised. Exit and rollback the changes
				self.rollbackTransaction()
				raise dException.QueryException, e

		self.commitTransaction()


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
					if isinstance(vv, (datetime.date, datetime.datetime)):
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
			
			newPKVal = None
			if newrec and self.AutoPopulatePK:
				# Some backends do not provide a means to retrieve 
				# auto-generated PKs; for those, we need to create the 
				# PK before inserting the record so that we can pass it on
				# to any linked child records.
				newPKVal = self.pregenPK()
				if newPKVal:
					self.setFieldVal(self.KeyField, newPKVal)
				
			#run the update
			res = self._getAuxCursor().execute(sql)
			
			if newrec and self.AutoPopulatePK and (newPKVal is None):
				# Call the database backend-specific code to retrieve the
				# most recently generated PK value.
				newPKVal = self.getLastInsertID()
				if newPKVal:
					self.setFieldVal(self.KeyField, newPKVal)

			if newrec:
				# Need to remove the new flag
				del rec[k.CURSOR_NEWFLAG]
			else:
				if not res:
					# Different backends may cause res to be None
					# even if the save is successful.
					self._getBackendObject().noResultsOnSave()
			rec[k.CURSOR_MEMENTO].setMemento(rec)

	
	def pregenPK(self):
		"""Various backend databases require that you manually 
		generate new PKs if you need to refer to their values afterward.
		This method will call the backend to generate and 
		retrieve a new PK if the backend supports this. We use the 
		auxiliary cursor so as not to alter the current data.
		"""
		return self._getBackendObject().pregenPK(self._getAuxCursor())
		
		
	def makeUpdDiff(self, rec, isnew=False):
		mem = rec[k.CURSOR_MEMENTO]
		ret = mem.makeDiff(rec, isnew)
		for fld in self.getNonUpdateFields():
			if ret.has_key(fld):
				del ret[fld]
		return ret		
		

	def new(self):
		""" Add a new record to the data set."""
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
		""" Revert any changes to the data set back to the original values."""
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
		if newrec:
			res = True
		else:
			pkWhere = self.makePkWhere()
			# some backends(PostgreSQL) don't return information about number of deleted rows
			# try to fetch it before
			sql = "select count(*) as cnt from %s where %s" % (self.Table, pkWhere)
			aux = self._getAuxCursor()
			aux.execute(sql)
			res = aux.getFieldVal('cnt')
			if res:
				sql = "delete from %s where %s" % (self.Table, pkWhere)
				aux.execute(sql)


		if not res:
			# Nothing was deleted
			self._getBackendObject().noResultsOnDelete()
		else:
			# Delete the record from the current dataset
			self.removeRow(delRowNum)
	
	
	def removeRow(self, r):
		""" Since record sets are tuples and thus immutable, we
		need to do this little dance to remove a row.
		"""
		lRec = list(self._records)
		del lRec[r]
		self._records = tuple(lRec)
		self.RowNumber = min(self.RowNumber, self.RowCount-1)
	
	
	def flush(self):
		""" Some backends need to be prompted to flush changes
		to disk even without starting a transaction. This is the method
		to call to accomplish this.
		"""
		self._getBackendObject().flush(self)


	def setDefaults(self, vals):
		"""Set the default field values for newly added records.

		The 'vals' parameter is a dictionary of fields and their default values.
		"""
		# The memento must be updated afterwards, since these should not count
		# as changes to the original values. 
		row = self._records[self.RowNumber]
		for kk, vv in vals.items():
			if row.has_key(kk):
				# try to execute it as a function, else assume it is a literal value:
				try:
					vv = vv()
				except:
					pass
				row[kk] = vv
			else:
				# We probably shouldn't add an erroneous field name to the row
				raise ValueError, "Can't set default value for nonexistent field '%s'." % kk
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
		"""Get the empty description from the backend object, 
		as different backends handle empty recordsets differently.
		"""
		dscrp = self._getBackendObject().getStructureDescription(self)
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
		compString = isinstance(sortList[0][0], basestring)

		if not compString:
			# coerce val to be the same type as the field type
			if isinstance(sortList[0][0], int):
				try:
					val = int(val)
				except ValueError:
					val = int(0)

			elif isinstance(sortList[0][0], long):
				try:
					val = long(val)
				except ValueError:
					val = long(0)

			elif isinstance(sortList[0][0], float):
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
		tblPrefix = self._getBackendObject().getWhereTablePrefix(self.Table)
		if not rec:
			rec = self._records[self.RowNumber]
		aFields = self.KeyField.split(",")

		if k.CURSOR_MEMENTO in rec:
			mem = rec[k.CURSOR_MEMENTO]
			getPkVal = lambda fld: mem.getOrigVal(fld)
		else:
			getPkVal = lambda fld: rec[fld]
			
		ret = ""
		for fld in aFields:
			if ret:
				ret += " AND "
			pkVal = getPkVal(fld)
			if isinstance(pkVal, basestring):
				ret += tblPrefix + fld + "='" + pkVal.encode(self.Encoding) + "' "
			else:
				ret += tblPrefix + fld + "=" + str(pkVal) + " "
		return ret


	def makeUpdClause(self, diff):
		""" Create the 'set field=val' section of the Update statement. 
		"""
		ret = ""
		tblPrefix = self._getBackendObject().getUpdateTablePrefix(self.Table)
		
		for fld, val in diff.items():
			# Skip the fields that are not to be updated.
			if fld in self.getNonUpdateFields():
				continue
			if ret:
				ret += ", "
			
			if isinstance(val, basestring):
				escVal = self.escQuote(val)
				ret += tblPrefix + fld + " = " + escVal + " "
			else:
				if isinstance(val, (datetime.date, datetime.datetime)):
					ret += tblPrefix + fld + " = " + self.formatDateTime(val)
				else:
					ret += tblPrefix + fld + " = " + str(val) + " "
		return ret


	def processFields(self, txt):
		return self._getBackendObject().processFields(txt)
		
	
	def escQuote(self, val):
		""" Escape special characters in SQL strings. """
		ret = val
		if isinstance(val, basestring):
			ret = self._getBackendObject().escQuote(val)
		return ret          


	def getTables(self, includeSystemTables=False):
		""" Return a tuple of tables in the current database.
		"""
		return self._getBackendObject().getTables(includeSystemTables)
		
	def getTableRecordCount(self, tableName):
		""" Get the number of records in the backend table.
		"""
		return self._getBackendObject().getTableRecordCount(tableName)
		
	def getFields(self, tableName=None):
		""" Get field information about the backend table.
		
		Returns a list of 3-tuples, where the 3-tuple's elements are:
			0: the field name (string)
			1: the field type ('I', 'N', 'C', 'M', 'B', 'D', 'T')
			2: boolean specifying whether this is a pk field.
		"""
		if tableName is None:
			# Use the default
			tableName = self.Table
		return self._getBackendObject().getFields(tableName)
	
	
	def getLastInsertID(self):
		""" Return the most recently generated PK """
		ret = None
		if self._getBackendObject():
			# Should we pass 'self' or 'self._getAuxCursor()'?
			ret = self._getBackendObject().getLastInsertID(self)
		return ret

	
	def formatDateTime(self, val):
		""" Format DateTime values for the backend """
		ret = val
		if self._getBackendObject():
			ret = self._getBackendObject().formatDateTime(val)
		return ret


	def beginTransaction(self):
		""" Begin a SQL transaction."""
		ret = None
		if self._getBackendObject():
			ret = self._getBackendObject().beginTransaction(self._getAuxCursor())
		return ret


	def commitTransaction(self):
		""" Commit a SQL transaction."""
		ret = None
		if self._getBackendObject():
			ret = self._getBackendObject().commitTransaction(self._getAuxCursor())
		return ret


	def rollbackTransaction(self):
		""" Roll back (revert) a SQL transaction."""
		ret = None
		if self._getBackendObject():
			ret = self._getBackendObject().rollbackTransaction(self._getAuxCursor())
		return ret
	

	###     SQL Builder methods     ########
	def getFieldClause(self):
		""" Get the field clause of the sql statement.
		"""
		return self.sqlManager._fieldClause

	def setFieldClause(self, clause):
		""" Set the field clause of the sql statement.
		"""
		self.sqlManager._fieldClause = self.sqlManager._getBackendObject().setFieldClause(clause)

	def addField(self, exp):
		""" Add a field to the field clause.
		"""
		if self.sqlManager._getBackendObject():
			self.sqlManager._fieldClause = self.sqlManager._getBackendObject().addField(self.sqlManager._fieldClause, exp)
		return self.sqlManager._fieldClause

	def getFromClause(self):
		""" Get the from clause of the sql statement.
		"""
		return self.sqlManager._fromClause

	def setFromClause(self, clause):
		""" Set the from clause of the sql statement.
		"""
		self.sqlManager._fromClause = self.sqlManager._getBackendObject().setFromClause(clause)

	def addFrom(self, exp):
		""" Add a table to the sql statement.

		For joins, use setFromClause() to set the entire from clause
		explicitly.
		"""
		if self.sqlManager._getBackendObject():
			self.sqlManager._fromClause = self.sqlManager._getBackendObject().addFrom(self.sqlManager._fromClause, exp)
		return self.sqlManager._fromClause


	def getWhereClause(self):
		""" Get the where clause of the sql statement.
		"""
		return self.sqlManager._whereClause

	def setWhereClause(self, clause):
		""" Set the where clause of the sql statement.
		"""
		self.sqlManager._whereClause = self.sqlManager._getBackendObject().setWhereClause(clause)

	def addWhere(self, exp, comp="and"):
		""" Add an expression to the where clause.
		"""
		if self.sqlManager._getBackendObject():
			self.sqlManager._whereClause = self.sqlManager._getBackendObject().addWhere(self.sqlManager._whereClause, exp, comp)
		return self.sqlManager._whereClause

	def prepareWhere(self, clause):
		""" Modifies WHERE clauses as needed for each backend. """
		return self.sqlManager._getBackendObject().prepareWhere(clause)
		
	def getChildFilterClause(self):
		""" Get the child filter part of the sql statement.
		"""
		return self.sqlManager._childFilterClause

	def setChildFilterClause(self, clause):
		""" Set the child filter clause of the sql statement.
		"""
		self.sqlManager._childFilterClause = self.sqlManager._getBackendObject().setChildFilterClause(clause)

	def getGroupByClause(self):
		""" Get the group-by clause of the sql statement.
		"""
		return self.sqlManager._groupByClause

	def setGroupByClause(self, clause):
		""" Set the group-by clause of the sql statement.
		"""
		self.sqlManager._groupByClause = self.sqlManager._getBackendObject().setGroupByClause(clause)

	def addGroupBy(self, exp):
		""" Add an expression to the group-by clause.
		"""
		if self.sqlManager._getBackendObject():
			self.sqlManager._groupByClause = self.sqlManager._getBackendObject().addGroupBy(self.sqlManager._groupByClause, exp)
		return self.sqlManager._groupByClause

	def getOrderByClause(self):
		""" Get the order-by clause of the sql statement.
		"""
		return self.sqlManager._orderByClause

	def setOrderByClause(self, clause):
		""" Set the order-by clause of the sql statement.
		"""
		self.sqlManager._orderByClause = self.sqlManager._getBackendObject().setOrderByClause(clause)

	def addOrderBy(self, exp):
		""" Add an expression to the order-by clause.
		"""
		if self.sqlManager._getBackendObject():
			self.sqlManager._orderByClause = self.sqlManager._getBackendObject().addOrderBy(self.sqlManager._orderByClause, exp)
		return self.sqlManager._orderByClause

	def getLimitClause(self):
		""" Get the limit clause of the sql statement.
		"""
		return self.sqlManager._limitClause

	def setLimitClause(self, clause):
		""" Set the limit clause of the sql statement.
		"""
		self.sqlManager._limitClause = clause

	def getLimitWord(self):
		""" Return the word to use in the db-specific limit clause.
		"""
		ret = "limit"
		if self.sqlManager._getBackendObject():
			ret = self.sqlManager._getBackendObject().getLimitWord()
		return ret
			
	def getLimitPosition(self):
		""" Return the position to place the limit clause.
		
		For currently-supported dbapi's, the return values of 'top' or 'bottom'
		are sufficient.
		"""
		ret = "bottom"
		if self.sqlManager._getBackendObject():
			ret = self.sqlManager._getBackendObject().getLimitPosition()
		return ret			
			
	def getSQL(self):
		""" Get the complete SQL statement from all the parts.
		"""
		fieldClause = self.sqlManager._fieldClause
		fromClause = self.sqlManager._fromClause
		whereClause = self.sqlManager._whereClause
		childFilterClause = self.sqlManager._childFilterClause
		groupByClause = self.sqlManager._groupByClause
		orderByClause = self.sqlManager._orderByClause
		limitClause = self.sqlManager._limitClause

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
			fromClause = "from " + self.sqlManager.Table
		if whereClause:
			whereClause = "where " + whereClause
		if groupByClause:
			groupByClause = "group by " + groupByClause
		if orderByClause:
			orderByClause = "order by " + orderByClause
		if limitClause:
			limitClause = "%s %s" % (self.sqlManager.getLimitWord(), limitClause)
		else:
			limitClause = "%s %s" % (self.sqlManager.getLimitWord(), self.sqlManager._defaultLimit)

		return self.sqlManager._getBackendObject().formSQL(fieldClause, fromClause, 
				whereClause, groupByClause, orderByClause, limitClause)
		

	def getStructureOnlySql(self):
		holdWhere = self.sqlManager._whereClause
		self.sqlManager.setWhereClause("1 = 0")
		ret = self.sqlManager.getSQL()
		self.sqlManager.setWhereClause(holdWhere)
		return ret

	def executeSQL(self, *args, **kwargs):
		self.sqlManager.execute(self.sqlManager.getSQL(), *args, **kwargs)
	###     end - SQL Builder methods     ########
	
	
	def getWordMatchFormat(self):
		return self.sqlManager._getBackendObject().getWordMatchFormat()

	def _getAuxCursor(self):
		if self.__auxCursor is None:
			if self._cursorFactoryClass is not None:
				if self._cursorFactoryFunc is not None:
					self.__auxCursor = self._cursorFactoryFunc(self._cursorFactoryClass)
		if not self.__auxCursor:
			self.__auxCursor = self._getBackendObject().getCursor(self.__class__)
		return self.__auxCursor
	
	def setBackendObject(self, obj):
		self.__backend = obj
		self._getAuxCursor().__backend = obj
	
	def _getBackendObject(self):
		return self.__backend


	## Property getter/setter methods ##
	def _getAutoSQL(self):
		return self.getSQL()

	def _getAutoPopulatePK(self):
		try:
			return self._autoPopulatePK
		except AttributeError:
			return True
	def _setAutoPopulatePK(self, autopop):
		self._autoPopulatePK = bool(autopop)
		
	def _getCurrentSQL(self):
		if self.UserSQL is not None:
			return self.UserSQL
		return self.AutoSQL

	def _getEncoding(self):
		return self._getBackendObject().Encoding
	
	def _getDescrip(self):
		return self.__backend.getDescription(self)
			
	def _getKeyField(self):
		try:
			return self._keyField
		except AttributeError:
			return ""

	def _getLastSQL(self):
		try:
			v = self._lastSQL
		except AttributeError:
			v = self._lastSQL = None
		return v
			
	def _setKeyField(self, kf):
		self._keyField = str(kf)
		self._getAuxCursor()._keyField = str(kf)
		self._keyFieldSet = True

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
		self._getAuxCursor()._table = str(table)
		if not self._keyFieldSet:
			# Get the PK field, if any
			try:
				self._keyField = [fld[0] for fld in self.getFields(table)
						if fld[2] ][0]	
			except: pass
	

	def _getUserSQL(self):
		try:
			v = self._userSQL
		except AttributeError:
			v = self._userSQL = None
		return v

	def _setUserSQL(self, val):
		self._userSQL = val


	def _isAdding(self):
		""" Return True if the current record is a new record.
		"""
		return self._records[self.RowNumber].has_key(k.CURSOR_NEWFLAG)
	
	AutoSQL = property(_getAutoSQL, None, None,
			_("Returns the SQL statement automatically generated by the sql manager."))

	AutoPopulatePK = property(_getAutoPopulatePK, _setAutoPopulatePK, None,
			_("When inserting a new record, does the backend populate the PK field?")) 
	
	CurrentSQL = property(_getCurrentSQL, None, None,
			_("Returns the current SQL that will be run, which is one of UserSQL or AutoSQL."))

	Encoding = property(_getEncoding, None, None,
			_("Encoding type used by the Backend  (string)") )
			
	FieldDescription = property(_getDescrip, None, None,
			_("Tuple of field names and types, as returned by the backend  (tuple)") )
			
	IsAdding = property(_isAdding, None, None,
			_("Returns True if the current record is new and unsaved"))
			
	LastSQL = property(_getLastSQL, None, None,
			_("Returns the last executed SQL statement."))

	KeyField = property(_getKeyField, _setKeyField, None,
			_("Name of field that is the PK. If multiple fields make up the key, "
			"separate the fields with commas. (str)"))
	
	RowNumber = property(_getRowNumber, _setRowNumber, None,
			_("Current row in the recordset."))
	
	RowCount = property(_getRowCount, None, None,
			_("Current number of rows in the recordset. Read-only."))

	Table = property(_getTable, _setTable, None,
			_("The name of the table in the database that this cursor is updating."))
			
	UserSQL = property(_getUserSQL, _setUserSQL, None,
			_("SQL statement to run. If set, the automatic SQL builder will not be used."))
