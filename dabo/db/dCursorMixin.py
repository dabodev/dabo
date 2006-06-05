import types
import datetime
import inspect
import random
import sys
import re
# Make sure that the user's installation supports Decimal.
_USE_DECIMAL = True
try:
	from decimal import Decimal
except ImportError:
	_USE_DECIMAL = False
# We also need to know if sqlite is installed
_useSQLite = True
try:
	from pysqlite2 import dbapi2 as sqlite
except ImportError:
	_useSQLite = False

import dabo
import dabo.dConstants as kons
from dabo.db.dMemento import dMemento
from dabo.dLocalize import _
import dabo.dException as dException
from dabo.dObject import dObject
from dabo.db import dNoEscQuoteStr
from dabo.db import dTable


class dCursorMixin(dObject):
	_call_initProperties = False
	def __init__(self, sql="", *args, **kwargs):
		self._initProperties()
		if sql and isinstance(sql, basestring) and len(sql) > 0:
			self.UserSQL = sql

		#self.super()
		#super(dCursorMixin, self).__init__()
		## pkm: Neither of the above are correct. We need to explicitly
		##      call dObject's __init__, otherwise the cursor object with
		##      which we are mixed-in will take the __init__.
		dObject.__init__(self, *args, **kwargs)
		
		# Just in case this is used outside of the context of a bizobj
		if not hasattr(self, "superCursor") or self.superCursor is None:
			myBases = self.__class__.__bases__
			for base in myBases:
				# Find the first base class that doesn't have the 'autoPopulatePK'
				# attribute. Designate that class as the superCursor class.
				if hasattr(base, "fetchall"):
					self.superCursor = base
					break


	def _initProperties(self):
		# Holds the dict used for adding new blank records
		self._blank = {}
		# Writable version of the dbapi 'description' attribute
		self.descriptionClean = None
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
		self._records = DataSet()
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

		self.initProperties()


	def setCursorFactory(self, func, cls):
		self._cursorFactoryFunc = func
		self._cursorFactoryClass = cls
		
	
	def setSQL(self, sql):
		pass
		# This function isn't needed anymore
		#self.sql = self.BackendObject.setSQL(sql)


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


	def execute(self, sql, params=(), useAuxCursor=None):
		"""The idea here is to let the super class do the actual work in 
		retrieving the data. However, many cursor classes can only return 
		row information as a list, not as a dictionary. This method will 
		detect that, and convert the results to a dictionary.

		The useAuxCursor argument specifies whether the sql will be executed
		using the main cursor or an auxiliary cursor. The possible values 
		are:
			None (default): The method will automatically determine what to do.
			True: An AuxCursor will be used
			False: The main cursor will be used (could be dangerous)
		"""
		#### NOTE: NEEDS TO BE TESTED THOROUGHLY!!!!  ####
		if useAuxCursor is None:
			if sql.strip().split()[0].lower() == "select":
				cursorToUse = self
			else:
				cursorToUse = self.AuxCursor
				#cursorToUse.AutoCommit = self.AutoCommit
		elif useAuxCursor:
			cursorToUse = self.AuxCursor
		else:
			cursorToUse = self
			
		# Some backends, notably Firebird, require that fields be specially
		# marked.
		sql = self.processFields(sql)
		
		# Make sure all Unicode characters are properly encoded.
		if isinstance(sql, unicode):
			sqlEX = sql.encode(self.Encoding)
		else:
			sqlEX = sql
		
		try:
			if params is None or len(params) == 0:
				res = cursorToUse.superCursor.execute(cursorToUse, sqlEX)
			else:
				res = cursorToUse.superCursor.execute(cursorToUse, sqlEX, params)
		except Exception, e:
			# If this is due to a broken connection, let the user know.
			# Different backends have different messages, but they
			# should all contain the string 'connect' in them.
			if "connect" in str(e).lower():
				raise dException.ConnectionLostException, e
			if "access" in str(e).lower():
				raise dException.DBNoAccessException(e)
			else:
				raise dException.DBQueryException(e, sql)
		
		if cursorToUse is not self:
			# No need to manipulate the data
			return res
	
		# Not all backends support 'fetchall' after executing a query
		# that doesn't return records, such as an update.
		try:
			self._records = DataSet(self.fetchall())
		except:
			pass
		
		# Some backend programs do odd things to the description
		# This allows each backend to handle these quirks individually.
		self.BackendObject.massageDescription(self)
		if self.RowCount > 0:
			self.RowNumber = max(0, self.RowNumber)
			maxrow = max(0, (self.RowCount-1) )
			self.RowNumber = min(self.RowNumber, maxrow)

		if self._records:
			if isinstance(self._records[0], tuple) or isinstance(self._records[0], list):
				# Need to convert each row to a Dict
				tmpRows = []
				# First, get the descriptionClean attribute and extract 
				# the field names from that
				fldNames = []
				for fld in self.FieldDescription:
					### 2006.01.26: egl - Removed the lower() function, which was preventing
					### this from working with case-sensitive backends. I can't recall why it was 
					### ever added, so I'm leaving it here commented out in case we run into
					### something that explains the need for this.
					#fldNames.append(fld[0].lower())
					fldNames.append(fld[0])
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
				self._records = DataSet(tmpRows)
			else:
				# Make all string values into unicode
				for row in self._records:
					for fld in row.keys():
						val = row[fld]
						if isinstance(val, str):	
							# String; convert it to unicode
							try:
								row[fld]= unicode(val, self.Encoding)
							except UnicodeDecodeError, e:
								# Try some common encodings:
								ok = False
								for enc in ("utf8", "latin-1"):
									if enc != self.Encoding:
										try:
											row[fld]= unicode(val, enc)
											ok = True
										except UnicodeDecodeError:
											continue
										if ok:
											# change self.Encoding and log the message
											self.Encoding = enc
											dabo.errorLog.write(_("Incorrect unicode encoding set; using '%s' instead")
											% enc)
											break
								else:
									raise UnicodeDecodeError, e

			# Convert to DataSet 
			self._records = DataSet(self._records)
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


	def storeFieldTypes(self, target=None):
		"""Stores the data type for each column in the result set."""
		if target is None:
			target = self
		if self.RowCount > 0:
			rec = self._records[0]
			for fname, fval in rec.items():
				target._types[fname] = type(fval)
		else:
			# See if we already have the information from a prior query
			if len(self._types.keys()) == 0:
				dabo.errorLog.write(_("RowCount is %s, so storeFieldTypes() can't run as implemented.") % self.RowCount)

	
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
		kf = self.KeyField
		if not self.__unsortedRows:
			# Record the PK values
			for row in self._records:
				if self._compoundKey:
					key = tuple([row[k] for k in kf])
					self.__unsortedRows.append(key)
				else:
					self.__unsortedRows.append(row[self.KeyField])

		# First, preserve the PK of the current row so that we can reset
		# the RowNumber property to point to the same row in the new order.
		try:
			if self._compoundKey:
				currRow = self._records[self.RowNumber]
				currRowKey = tuple([currRow[k] for k in kf])
			else:
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
				if self._compoundKey:
					key = tuple([row[k] for k in kf])
					sortList.append([self.__unsortedRows.index(key), row])
				else:
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

		# can't compare NoneType to some types: sort None lower than anything else:
		def noneSort(vv, ww):
			xx, yy = vv[0], ww[0]
			if xx is None and yy is None:
				return 0
			elif xx is None and yy is not None:
				return -1
			elif xx is not None and yy is None:
				return 1
			else:
				return cmp(xx, yy)

		def caseInsensitiveSort(vv, ww):
			vv, ww = vv[0], ww[0]
			if vv is None:
				vv = ""
			if ww is None:
				ww = ""
			return cmp(vv.lower(), ww.lower())

		if compString and not caseSensitive:
			sortfunc = caseInsensitiveSort
		else:
			sortfunc = noneSort	
		sortList.sort(sortfunc)
			
		# Unless DESC was specified as the sort order, we're done sorting
		if ord == "DESC":
			sortList.reverse()
		# Extract the rows into a new list, then convert them back to the _records tuple
		newRows = []
		for elem in sortList:
			newRows.append(elem[1])
		self._records = DataSet(newRows)

		# restore the RowNumber
		if currRowKey:
			for ii in range(0, self.RowCount):
				row = self._records[ii]
				if self._compoundKey:
					key = tuple([row[k] for k in kf])
					found = (key == currRowKey)
				else:
					found = row[self.KeyField] == currRowKey
				if found:
					self.RowNumber = ii
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

	def setNonUpdateFields(self, fldList=None):
		if fldList is None:
			fldList = []
		self.nonUpdateFields = fldList
	
	
	def getNonUpdateFields(self):
		return self.nonUpdateFields + self.__nonUpdateFields
		
		
	def __setNonUpdateFields(self):
		"""Delegate this to the backend object."""
		self.BackendObject.setNonUpdateFields(self)
	

	def isChanged(self, allRows=True):
		"""Scan all the records and compare them with their mementos. 
		Returns True if any differ, False otherwise.
		"""
		ret = False
		if self.RowCount > 0:
			if allRows:
				recs = self._records
			else:
				recs = (self._records[self.RowNumber],)

			for ii in range(len(recs)):
				rec = recs[ii]
				if self.isRowChanged(rec):
					ret = True
					break
		return ret


	def isRowChanged(self, rec):
		ret = False
		if rec.has_key(kons.CURSOR_MEMENTO):
			mem = rec[kons.CURSOR_MEMENTO]
			newrec = rec.has_key(kons.CURSOR_NEWFLAG)
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
		kf = self.KeyField
		if isinstance(kf, tuple):
			for key in kf:
				rec[key] = tmpPK
		else:
			rec[kf] = tmpPK
		rec[kons.CURSOR_TMPKEY_FIELD] = tmpPK
		
	
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
		is new an unsaved record, return the temp PK value. If this is a compound 
		PK, return a tuple containing each field's values.
		"""
		ret = None
		if self.RowCount <= 0:
			raise dException.NoRecordsException, _("No records in the data set.")
		rec = self._records[self.RowNumber]
		if rec.has_key(kons.CURSOR_NEWFLAG) and self.AutoPopulatePK:
			# New, unsaved record
			ret = rec[kons.CURSOR_TMPKEY_FIELD]
		else:
			kf = self.KeyField
			if isinstance(kf, tuple):
				ret = tuple([rec[k] for k in kf])
			else:
				ret = rec[kf]
		return ret
		

	def getFieldVal(self, fld, row=None):
		""" Return the value of the specified field in the current or specified row."""
		ret = None
		if self.RowCount <= 0:
			raise dException.NoRecordsException, _("No records in the data set.")
		if row is None:
			row = self.RowNumber

		rec = self._records[row]
		if isinstance(fld, (tuple, list)):
			ret = []
			for xFld in fld:
				ret.append(self.getFieldVal(xFld, row=row))
			ret = tuple(ret)
		else:
			if rec.has_key(fld):
				ret = rec[fld]
			else:
				raise dException.dException, "%s '%s' %s" % (
						_("Field"), fld, _("does not exist in the data set"))
		return ret


	def _fldTypeFromDB(self, fld):
		"""Try to determine the field type from the database information
		If the field isn't found, return None.
		"""
		ret = None
		flds = self.getFields()
		try:
			typ = [ff[1] for ff in flds if ff[0] == fld][0]
		except IndexError:
			# This 'fld' value is not a native field, so no way to 
			# determine its type
			typ = None
		if typ:
			try:
				ret = {"C" : str, "D" : datetime.date, "B" : bool, 
					"N" : float, "M" : str, "I" : int, "T" : datetime.datetime}[typ]
			except KeyError:
				ret = None
		return ret
		

	def setFieldVal(self, fld, val):
		""" Set the value of the specified field. """
		if self.RowCount <= 0:
			raise dException.dException, _("No records in the data set")
		else:
			rec = self._records[self.RowNumber]
			if rec.has_key(fld):
				if self._types.has_key(fld):
					fldType = self._types[fld]
				else:
					fldType = self._fldTypeFromDB(fld)
				if fldType is not None:
					if fldType != type(val):
						convTypes = (str, unicode, int, float, long, complex)
						if isinstance(val, convTypes) and isinstance(rec[fld], basestring):
							if isinstance(fldType, str):
								val = str(val)
							else:
								val = unicode(val)
						elif isinstance(rec[fld], int) and isinstance(val, bool):
							# convert bool to int (original field val was bool, but UI
							# changed to int. 
							val = int(val)
						elif isinstance(rec[fld], int) and isinstance(val, long):
							# convert long to int (original field val was int, but UI
							# changed to long. 
							val = int(val)
						elif isinstance(rec[fld], long) and isinstance(val, int):
							# convert int to long (original field val was long, but UI
							# changed to int. 
							val = long(val)

					if fldType != type(val):
						ignore = False
						# Date and DateTime types are handled as character, even if the 
						# native field type is not. Ignore these. NOTE: we have to deal with the 
						# string representation of these classes, as there is no primitive for either
						# 'DateTime' or 'Date'.
						dtStrings = ("<type 'DateTime'>", "<type 'Date'>", "<type 'datetime.datetime'>")
						if str(fldType) in dtStrings and isinstance(val, basestring):
								ignore = True
						elif val is None or fldType is type(None):
							# Any field type can potentially hold None values (NULL). Ignore these.
							ignore = True
						elif isinstance(val, dNoEscQuoteStr.dNoEscQuoteStr):
							# Sometimes you want to set it to a sql function, equation, ect.
							ignore = True
						else:
							# This can also happen with a new record, since we just stuff the
							# fields full of empty strings.
							ignore = self._records[self.RowNumber].has_key(kons.CURSOR_NEWFLAG)
						
						if not ignore:
							msg = _("!!! Data Type Mismatch: field=%s. Expecting: %s; got: %s") \
									% (fld, str(fldType), str(type(val)))
							dabo.errorLog.write(msg)
				rec[fld] = val

			else:
				ss = _("Field '%s' does not exist in the data set.") % (fld,)
				raise dException.dException, ss


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
			mem = row[kons.CURSOR_MEMENTO]
		except:
			# Either there isn't any such row number, or it doesn't have a 
			# memento. Either way, return an empty dict
			return {}
		diff = mem.makeDiff(row, isNewRecord=row.has_key(kons.CURSOR_NEWFLAG))
		ret = {}
		for kk, vv in diff:
			ret[kk] = (mem.getOrigVal(kk), vv)
		return ret


	def getCurrentRecord(self):
		"""Returns the current record (as determined by self.RowNumber)
		as a dict, or None if the RowNumber is not a valid record.
		"""
		try:
			ret = self.getDataSet(rowStart=self.RowNumber, rows=1)[0]
		except IndexError:
			ret = None
		return ret
		
		
	def getDataSet(self, flds=(), rowStart=0, rows=None, 
			returnInternals=False):
		""" Get the entire data set encapsulated in a list. 

		If the optional	'flds' parameter is given, the result set will be filtered 
		to only include the specified fields. rowStart specifies the starting row
		to include, and rows is the number of rows to return. 
		"""
		try:
			if rows is not None:
				tmp = self._records[rowStart:rowStart+rows]
			else:
				tmp = self._records[rowStart:]
			# The dicts in the returned dat set need to be copied; 
			# otherwise, modifying the data set will modify this 
			# cursor's records!
			ret = [tmprec.copy() for tmprec in tmp]
		except AttributeError:
			# return empty dataset
			return DataSet()

		internals = (kons.CURSOR_MEMENTO, kons.CURSOR_NEWFLAG, 
				kons.CURSOR_TMPKEY_FIELD)

		for rec in ret:
			if not flds and not returnInternals:
				# user didn't specify explicit fields and doesn't want internals
				for internal in internals:
					if rec.has_key(internal):
						del rec[internal]
			if flds:
				# user specified specific fields - get rid of all others
				for k in rec.keys():
					if k not in flds:
						del rec[k]

		ret = DataSet(ret)
		return ret

	
	def replace(self, field, valOrExpr, scope=None):
		"""Replaces the value of the specified field with the given value
		or expression. All records matching the scope are affected; if
		no scope is specified, all records are affected.
		
		'valOrExpr' will be treated as a literal value, unless it is prefixed
		with an equals sign. All expressions will therefore be a string 
		beginning with '='. Literals can be of any type. 
		"""
		if isinstance(self._records, DataSet):
			self._records.replace(field, valOrExpr, scope=scope)
			

	def first(self):
		""" Move the record pointer to the first record of the data set."""
		if self.RowCount > 0:
			self.RowNumber = 0
		else:
			raise dException.NoRecordsException, _("No records in data set")


	def prior(self):
		""" Move the record pointer back one position in the recordset."""
		if self.RowCount > 0:
			if self.RowNumber > 0:
				self.RowNumber -= 1
			else:
				raise dException.BeginningOfFileException, _("Already at the beginning of the data set.")
		else:
			raise dException.NoRecordsException, _("No records in data set")


	def next(self):
		""" Move the record pointer forward one position in the recordset."""
		if self.RowCount > 0:
			if self.RowNumber < (self.RowCount-1):
				self.RowNumber += 1
			else:
				raise dException.EndOfFileException, _("Already at the end of the data set.")
		else:
			raise dException.NoRecordsException, _("No records in data set")


	def last(self):
		""" Move the record pointer to the last record in the recordset."""
		if self.RowCount > 0:
			self.RowNumber = self.RowCount-1
		else:
			raise dException.NoRecordsException, _("No records in data set")


	def save(self, allrows=False, useTransaction=False):
		""" Save any changes to the data back to the data store."""
		# Make sure that there is data to save
		if self.RowCount <= 0:
			raise dException.dException, _("No data to save")
		# Make sure that there is a PK
		self.checkPK()
		if allrows:
			recs = self._records
		else:
			recs = (self._records[self.RowNumber],)

		if useTransaction:
			self.beginTransaction()

		for rec in recs:
			try:
				self.__saverow(rec)
			except dException.DBQueryException, e:
				# Error was raised. Exit and rollback the changes if
				# this object started the transaction.
				if useTransaction:
					self.rollbackTransaction()
				raise dException.DBQueryException, e
			except StandardError, e:
				if "connect" in str(e).lower():
					raise dException.ConnectionLostException, e
				else:
					# Error was raised. Exit and rollback the changes if
					# this object started the transaction.
					if useTransaction:
						self.rollbackTransaction()
					raise dException.QueryException, e
		if useTransaction:
			self.commitTransaction()


	def __saverow(self, rec):
		newrec =  rec.has_key(kons.CURSOR_NEWFLAG)
		mem = rec[kons.CURSOR_MEMENTO]
		diff = self.makeUpdDiff(rec, newrec)

		if diff:
			if newrec:
				flds = ""
				vals = ""
				kf = self.KeyField
				for kk, vv in diff.items():
					if self.AutoPopulatePK:
						if self._compoundKey:
							skipIt = (kk in kf)
						else:
							skipIt = (kk == self.KeyField)
						if skipIt:
							# we don't want to include the PK in the insert
							continue
					if kk in self.getNonUpdateFields():
						# Skip it.
						continue
						
					# Append the field and its value.
					flds += ", " + kk
					
					# add value to expression
					vals += ", %s" % (self.formatForQuery(vv),)
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
				# to any linked child records. NOTE: if you are using 
				# compound PKs, this cannot be done.
				newPKVal = self.pregenPK()
				if newPKVal and not self._compoundKey:
					self.setFieldVal(self.KeyField, newPKVal)
				
			#run the update
			aux = self.AuxCursor
			res = aux.execute(sql)

			if newrec and self.AutoPopulatePK and (newPKVal is None):
				# Call the database backend-specific code to retrieve the
				# most recently generated PK value.
				newPKVal = aux.getLastInsertID()
				if newPKVal and not self._compoundKey:
					self.setFieldVal(self.KeyField, newPKVal)

			if newrec:
				# Need to remove the new flag
				del rec[kons.CURSOR_NEWFLAG]
			else:
				if not res:
					# Different backends may cause res to be None
					# even if the save is successful.
					self.BackendObject.noResultsOnSave()
			rec[kons.CURSOR_MEMENTO].setMemento(rec)

	
	def pregenPK(self):
		"""Various backend databases require that you manually 
		generate new PKs if you need to refer to their values afterward.
		This method will call the backend to generate and 
		retrieve a new PK if the backend supports this. We use the 
		auxiliary cursor so as not to alter the current data.
		"""
		return self.BackendObject.pregenPK(self.AuxCursor)
		
		
	def makeUpdDiff(self, rec, isnew=False):
		"""Returns only those fields that have changed."""
		mem = rec[kons.CURSOR_MEMENTO]
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
		self._records = DataSet(tmprows)
		# Adjust the RowCount and position
		self.RowNumber = self.RowCount - 1
		# Add the 'new record' flag to the last record (the one we just added)
		self._records[self.RowNumber][kons.CURSOR_NEWFLAG] = True
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
		kf = self.KeyField
		for rec in recs:
			if self._compoundKey:
				key = tuple([rec[k] for k in kf])
				cancelPKs.append(key)
			else:
				cancelPKs.append(rec[kf])

		for ii in range(self.RowCount-1, -1, -1):
			rec = self._records[ii]
			if self._compoundKey:
				key = tuple([rec[k] for k in kf])
			else:
				key = rec[self.KeyField]
				
			if key in cancelPKs:
				if not self.isRowChanged(rec):
					# Nothing to cancel
					continue

				newrec =  rec.has_key(kons.CURSOR_NEWFLAG)
				if newrec:
					# Discard the record, and adjust the props
					self.delete(ii)
				else:
					self.__cancelRow(rec)


	def __cancelRow(self, rec):
		mem = rec[kons.CURSOR_MEMENTO]
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
		newrec =  rec.has_key(kons.CURSOR_NEWFLAG)
		if newrec:
			res = True
		else:
			pkWhere = self.makePkWhere()
			# some backends(PostgreSQL) don't return information about number of deleted rows
			# try to fetch it before
			sql = "select count(*) as cnt from %s where %s" % (self.Table, pkWhere)
			aux = self.AuxCursor
			aux.execute(sql)
			res = aux.getFieldVal('cnt')
			if res:
				sql = "delete from %s where %s" % (self.Table, pkWhere)
				aux.execute(sql)


		if not res:
			# Nothing was deleted
			self.BackendObject.noResultsOnDelete()
		else:
			# Delete the record from the current dataset
			self.removeRow(delRowNum)
	
	
	def removeRow(self, rr):
		""" Since record sets are tuples and thus immutable, we
		need to do this little dance to remove a row.
		"""
		lRec = list(self._records)
		del lRec[rr]
		self._records = DataSet(lRec)
		self.RowNumber = min(self.RowNumber, self.RowCount-1)
	
	
	def flush(self):
		""" Some backends need to be prompted to flush changes
		to disk even without starting a transaction. This is the method
		to call to accomplish this.
		"""
		self.BackendObject.flush(self)


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
		row[kons.CURSOR_MEMENTO].setMemento(row)


	def addMemento(self, rownum=-1):
		""" Add a memento to the specified row. If the rownum is -1, 
		a memento will be added to all rows. 
		"""
		if rownum == -1:
			# Make sure that there are rows to process
			if self.RowCount < 1:
				return
			for ii in range(0, self.RowCount):
				self.addMemento(ii)
		row = self._records[rownum]
		if not row.has_key(kons.CURSOR_MEMENTO):
			row[kons.CURSOR_MEMENTO] = dMemento()
		# Take the snapshot of the current values
		row[kons.CURSOR_MEMENTO].setMemento(row, skipFields=self.getNonUpdateFields())


	def __setStructure(self):
		"""Get the empty description from the backend object, 
		as different backends handle empty recordsets differently.
		"""
		dscrp = self.BackendObject.getStructureDescription(self)
		for fld in dscrp:
			fldname = fld[0]
			try:
				typ = self._types[fldname]
				# Handle the non-standard cases
				if _USE_DECIMAL and typ is Decimal:
					newval = Decimal()
					# If the backend reports a decimal scale, use it. Scale refers to the
					# number of decimal places.
					scale = fld[5]
					if scale is not None:
						ex = "0.%s" % ("0"*scale)
						newval = newval.quantize(Decimal(ex))
				elif typ is datetime.datetime:
					newval = datetime.datetime.min
				elif typ is datetime.date:
					newval = datetime.date.min
				else:
					newval = typ()
			except StandardError, e:
				# Either the data types have not yet been defined, or 
				# it is a type that cannot be instantiated simply.
				dabo.errorLog.write(_("Failed to create newval for field '%s'") % fldname)
				dabo.errorLog.write("TYPES: %s" % self._types)
				dabo.errorLog.write(str(e))
				newval = ""
			self._blank[fldname] = newval

		# Mark the calculated and derived fields.
		self.__setNonUpdateFields()


	def moveToPK(self, pk):
		""" Find the record with the passed primary key, and make it active.

		If the record is not found, the position is set to the first record. 
		"""
		self.RowNumber = 0
		kf = self.KeyField
		for ii in range(0, len(self._records)):
			rec = self._records[ii]
			if self._compoundKey:
				key = tuple([rec[k] for k in kf])
			else:
				key = rec[self.KeyField]
			if key == pk:
				self.RowNumber = ii
				break


	def moveToRowNum(self, rownum):
		""" Move the record pointer to the specified row number.

		If the specified row does not exist, the pointer remains where it is, 
		and an exception is raised.
		"""
		if (rownum >= self.RowCount) or (rownum < 0):
			raise dException.dException, _("Invalid row specified.")
		self.RowNumber = rownum


	def seek(self, val, fld=None, caseSensitive=True, near=False, movePointer=True):
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
		for ii in range(0, self.RowCount):
			sortList.append( [self._records[ii][fld], ii] )

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
		if movePointer and ret > -1:
			# Move the record pointer
			self.RowNumber = ret
		return ret


	def checkPK(self):
		""" Verify that the field(s) specified in the KeyField prop exist."""
		# First, make sure that there is *something* in the field
		kf = self.KeyField
		if not kf:
			raise dException.dException, _("checkPK failed; no primary key specified")

		if isinstance(kf, basestring):
			kf = [kf]
		# Make sure that there is a field with that name in the data set
		try:
			for fld in kf:
				self._records[0][fld]
		except:
			raise dException.dException, _("Primary key field does not exist in the data set: ") + fld


	def makePkWhere(self, rec=None):
		""" Create the WHERE clause used for updates, based on the pk field. 

		Optionally pass in a record object, otherwise use the current record.
		"""
		tblPrefix = self.BackendObject.getWhereTablePrefix(self.Table)
		if not rec:
			rec = self._records[self.RowNumber]
		if self._compoundKey:
			keyFields = self.KeyField
		else:
			keyFields = [self.KeyField]

		if kons.CURSOR_MEMENTO in rec:
			mem = rec[kons.CURSOR_MEMENTO]
			getPkVal = lambda fld: mem.getOrigVal(fld)
		else:
			getPkVal = lambda fld: rec[fld]
			
		ret = ""
		for fld in keyFields:
			if ret:
				ret += " AND "
			pkVal = getPkVal(fld)
			if isinstance(pkVal, basestring):
				ret += tblPrefix + fld + "='" + pkVal.encode(self.Encoding) + "' "
			elif isinstance(pkVal, (datetime.date, datetime.datetime)):
				ret += tblPrefix + fld + "=" + self.formatDateTime(pkVal) + " "
			else:
				ret += tblPrefix + fld + "=" + str(pkVal) + " "
		return ret


	def makeUpdClause(self, diff):
		""" Create the 'set field=val' section of the Update statement. """
		ret = ""
		tblPrefix = self.BackendObject.getUpdateTablePrefix(self.Table)
		
		for fld, val in diff.items():
			# Skip the fields that are not to be updated.
			if fld in self.getNonUpdateFields():
				continue
			if ret:
				ret += ", "
			
			ret += tblPrefix + fld + " = " + self.formatForQuery(val)			
		return ret


	def processFields(self, txt):
		return self.BackendObject.processFields(txt)
		
	
	def escQuote(self, val):
		""" Escape special characters in SQL strings. """
		ret = val
		if isinstance(val, basestring):
			ret = self.BackendObject.escQuote(val)
		return ret          


	def getTables(self, includeSystemTables=False):
		""" Return a tuple of tables in the current database."""
		return self.BackendObject.getTables(includeSystemTables)
		
		
	def getTableRecordCount(self, tableName):
		""" Get the number of records in the backend table."""
		return self.BackendObject.getTableRecordCount(tableName)
		
		
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
		return self.BackendObject.getFields(tableName)
	

	def getFieldInfoFromDescription(self):
		""" Get field information from the cursor description.

		Returns a tuple of 3-tuples, where the 3-tuple's elements are:
			0: the field name (string)
			1: the field type ('I', 'N', 'C', 'M', 'B', 'D', 'T'), or None.
			2: boolean specifying whether this is a pk field, or None.
		"""
		return self.BackendObject.getFieldInfoFromDescription(self.descriptionClean)


	def getLastInsertID(self):
		""" Return the most recently generated PK """
		ret = None
		if self.BackendObject:
			ret = self.BackendObject.getLastInsertID(self)
		return ret

	
	def formatForQuery(self, val):
		""" Format any value for the backend """
		ret = val
		if self.BackendObject:
			ret = self.BackendObject.formatForQuery(val)
		return ret

	
	def formatDateTime(self, val):
		""" Format DateTime values for the backend """
		ret = val
		if self.BackendObject:
			ret = self.BackendObject.formatDateTime(val)
		return ret


	def formatNone(self):
		""" Format None values for the backend """
		if self.BackendObject:
			return self.BackendObject.formatNone()


	def beginTransaction(self):
		""" Begin a SQL transaction."""
		ret = None
		if self.BackendObject:
			if not self.AutoCommit:
				ret = self.BackendObject.beginTransaction(self.AuxCursor)
		return ret


	def commitTransaction(self):
		""" Commit a SQL transaction."""
		ret = None
		if self.BackendObject:
			if not self.AutoCommit:
				ret = self.BackendObject.commitTransaction(self.AuxCursor)
		return ret


	def rollbackTransaction(self):
		""" Roll back (revert) a SQL transaction."""
		ret = None
		if self.BackendObject:
			ret = self.BackendObject.rollbackTransaction(self.AuxCursor)
		return ret
	

	def createTable(self, tabledef):
		"""Create a table based on the table definition."""
		self.BackendObject.createJustTable(tabledef, self)
		
		
	def createIndexes(self, tabledef):
		"""Create indexes based on the table definition."""
		self.BackendObject.createJustIndexes(tabledef, self)
		
		
	def createTableAndIndexes(self, tabledef):
		"""Create a table and its indexes based on the table definition."""
		self.BackendObject.createTableAndIndexes(tabledef, self)


	###     SQL Builder methods     ########
	def getFieldClause(self):
		""" Get the field clause of the sql statement."""
		return self.sqlManager._fieldClause


	def setFieldClause(self, clause):
		""" Set the field clause of the sql statement."""
		self.sqlManager._fieldClause = self.sqlManager.BackendObject.setFieldClause(clause)


	def addField(self, exp):
		""" Add a field to the field clause."""
		if self.sqlManager.BackendObject:
			self.sqlManager._fieldClause = self.sqlManager.BackendObject.addField(self.sqlManager._fieldClause, exp)
		return self.sqlManager._fieldClause


	def getFromClause(self):
		""" Get the from clause of the sql statement."""
		return self.sqlManager._fromClause


	def setFromClause(self, clause):
		""" Set the from clause of the sql statement."""
		self.sqlManager._fromClause = self.sqlManager.BackendObject.setFromClause(clause)


	def addFrom(self, exp):
		""" Add a table to the sql statement.

		For joins, use setFromClause() to set the entire from clause
		explicitly.
		"""
		if self.sqlManager.BackendObject:
			self.sqlManager._fromClause = self.sqlManager.BackendObject.addFrom(self.sqlManager._fromClause, exp)
		return self.sqlManager._fromClause


	def getWhereClause(self):
		""" Get the where clause of the sql statement."""
		return self.sqlManager._whereClause


	def setWhereClause(self, clause):
		""" Set the where clause of the sql statement."""
		self.sqlManager._whereClause = self.sqlManager.BackendObject.setWhereClause(clause)


	def addWhere(self, exp, comp="and"):
		""" Add an expression to the where clause."""
		if self.sqlManager.BackendObject:
			self.sqlManager._whereClause = self.sqlManager.BackendObject.addWhere(self.sqlManager._whereClause, exp, comp)
		return self.sqlManager._whereClause


	def prepareWhere(self, clause):
		""" Modifies WHERE clauses as needed for each backend. """
		return self.sqlManager.BackendObject.prepareWhere(clause)
		
		
	def getChildFilterClause(self):
		""" Get the child filter part of the sql statement."""
		return self.sqlManager._childFilterClause


	def setChildFilterClause(self, clause):
		""" Set the child filter clause of the sql statement."""
		self.sqlManager._childFilterClause = self.sqlManager.BackendObject.setChildFilterClause(clause)


	def getGroupByClause(self):
		""" Get the group-by clause of the sql statement."""
		return self.sqlManager._groupByClause


	def setGroupByClause(self, clause):
		""" Set the group-by clause of the sql statement."""
		self.sqlManager._groupByClause = self.sqlManager.BackendObject.setGroupByClause(clause)


	def addGroupBy(self, exp):
		""" Add an expression to the group-by clause."""
		if self.sqlManager.BackendObject:
			self.sqlManager._groupByClause = self.sqlManager.BackendObject.addGroupBy(self.sqlManager._groupByClause, exp)
		return self.sqlManager._groupByClause


	def getOrderByClause(self):
		""" Get the order-by clause of the sql statement."""
		return self.sqlManager._orderByClause
		

	def setOrderByClause(self, clause):
		""" Set the order-by clause of the sql statement."""
		self.sqlManager._orderByClause = self.sqlManager.BackendObject.setOrderByClause(clause)


	def addOrderBy(self, exp):
		""" Add an expression to the order-by clause."""
		if self.sqlManager.BackendObject:
			self.sqlManager._orderByClause = self.sqlManager.BackendObject.addOrderBy(self.sqlManager._orderByClause, exp)
		return self.sqlManager._orderByClause


	def getLimitClause(self):
		""" Get the limit clause of the sql statement."""
		return self.sqlManager._limitClause
		

	def setLimitClause(self, clause):
		""" Set the limit clause of the sql statement."""
		self.sqlManager._limitClause = clause


	def getLimitWord(self):
		""" Return the word to use in the db-specific limit clause."""
		ret = "limit"
		if self.sqlManager.BackendObject:
			ret = self.sqlManager.BackendObject.getLimitWord()
		return ret
		
			
	def getLimitPosition(self):
		""" Return the position to place the limit clause.
		
		For currently-supported dbapi's, the return values of 'top' or 'bottom'
		are sufficient.
		"""
		ret = "bottom"
		if self.sqlManager.BackendObject:
			ret = self.sqlManager.BackendObject.getLimitPosition()
		return ret
		
			
	def getSQL(self):
		""" Get the complete SQL statement from all the parts."""
		fieldClause = self.sqlManager._fieldClause
		fromClause = self.sqlManager._fromClause
		whereClause = self.sqlManager._whereClause
		childFilterClause = self.sqlManager._childFilterClause
		groupByClause = self.sqlManager._groupByClause
		orderByClause = self.sqlManager._orderByClause
		limitClause = self.sqlManager._limitClause

		if not fieldClause:
			fieldClause = "*"
		
		if not fromClause:
			fromClause = self.Table
		
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

		return self.sqlManager.BackendObject.formSQL(fieldClause, fromClause, 
				whereClause, groupByClause, orderByClause, limitClause)
		

	def getStructureOnlySql(self):
		"""Creates a SQL statement that will not return any records."""
		holdWhere = self.sqlManager._whereClause
		self.sqlManager.setWhereClause("")
		holdLimit = self.sqlManager._limitClause
		self.sqlManager.setLimitClause(1)
		ret = self.sqlManager.getSQL()
		self.sqlManager.setWhereClause(holdWhere)
		self.sqlManager.setLimitClause(holdLimit)
		return ret
		

	def executeSQL(self, *args, **kwargs):
		self.sqlManager.execute(self.sqlManager.getSQL(), *args, **kwargs)
	###     end - SQL Builder methods     ########
	
	
	def getWordMatchFormat(self):
		return self.sqlManager.BackendObject.getWordMatchFormat()
		

	## Property getter/setter methods ##
	def _getAutoCommit(self):
		return self.BackendObject.getAutoCommitStatus(self)
		

	def _setAutoCommit(self, val):
		self.BackendObject.setAutoCommitStatus(self, val)


	def _getAutoSQL(self):
		return self.getSQL()
		

	def _getAutoPopulatePK(self):
		try:
			return self._autoPopulatePK
		except AttributeError:
			return True
			
	def _setAutoPopulatePK(self, autopop):
		self._autoPopulatePK = bool(autopop)


	def _getAuxCursor(self):
		if self.__auxCursor is None:
			if self._cursorFactoryClass is not None:
				if self._cursorFactoryFunc is not None:
					self.__auxCursor = self._cursorFactoryFunc(self._cursorFactoryClass)
		if not self.__auxCursor:
			self.__auxCursor = self.BackendObject.getCursor(self.__class__)
		return self.__auxCursor
	

	def _getBackendObject(self):
		return self.__backend

	def _setBackendObject(self, obj):
		self.__backend = obj
		self.AuxCursor.__backend = obj
	
		
	def _getCurrentSQL(self):
		if self.UserSQL is not None:
			return self.UserSQL
		return self.AutoSQL
		

	def _getDescrip(self):
		return self.__backend.getDescription(self)
		
			
	def _getEncoding(self):
		return self.BackendObject.Encoding
	
	def _setEncoding(self, val):
		self.BackendObject.Encoding = val
		
	
	def _getIsAdding(self):
		""" Return True if the current record is a new record."""
		return self._records[self.RowNumber].has_key(kons.CURSOR_NEWFLAG)
		
	
	def _getKeyField(self):
		try:
			return self._keyField
		except AttributeError:
			return ""

	def _setKeyField(self, kf):
		if "," in kf:
			self._keyField = tuple(kf.replace(" ", "").split(","))
			self._compoundKey = True
		else:
			self._keyField = str(kf)
			self._compoundKey = False
		self.AuxCursor._keyField = self._keyField
		self.AuxCursor._compoundKey = self._compoundKey
		self._keyFieldSet = True


	def _getLastSQL(self):
		try:
			v = self._lastSQL
		except AttributeError:
			v = self._lastSQL = None
		return v
		
			
	def _getRowNumber(self):
		try:
			return self.__rownumber
		except AttributeError:
			return -1
	
	def _setRowNumber(self, num):
		self.__rownumber = num
	

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
		self.AuxCursor._table = str(table)
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


	AutoCommit = property(_getAutoCommit, _setAutoCommit, None,
			_("Do we need explicit begin/commit/rollback commands for transactions?  (bool)"))
	
	AutoSQL = property(_getAutoSQL, None, None,
			_("Returns the SQL statement automatically generated by the sql manager."))

	AutoPopulatePK = property(_getAutoPopulatePK, _setAutoPopulatePK, None,
			_("When inserting a new record, does the backend populate the PK field?")) 
	
	AuxCursor = property(_getAuxCursor, None, None,
			_("""Auxiliary cursor object that handles queries that would otherwise
			affect the main cursor's data set.  (dCursorMixin subclass)""")) 
	
	BackendObject = property(_getBackendObject, _setBackendObject, None,
			_("Returns a reference to the object defining backend-specific behavior (dBackend)")) 
	
	CurrentSQL = property(_getCurrentSQL, None, None,
			_("Returns the current SQL that will be run, which is one of UserSQL or AutoSQL."))

	Encoding = property(_getEncoding, _setEncoding, None,
			_("Encoding type used by the Backend  (string)") )
			
	FieldDescription = property(_getDescrip, None, None,
			_("Tuple of field names and types, as returned by the backend  (tuple)") )
			
	IsAdding = property(_getIsAdding, None, None,
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



class DataSetOld(tuple):
	""" This class assumes that its contents are not ordinary tuples, but
	rather tuples consisting of dicts, where the dict keys are field names.
	This is the data structure returned by the dCursorMixin class.
	"""
	# List comprehensions used in this class require a non-conflicting 
	# name. This is unlikely to be used anywhere else.
	_dictSubName = "_dataSet_rec"
	
	
	def _fldReplace(self, expr, dictName=None):
		"""The list comprehensions require the field names be the keys
		in a dictionary expression. Users, though, should not have to know
		about this. This takes a user-defined, SQL-like expressions, and 
		substitutes any field name with the corresponding dict
		expression.
		"""
		keys = self[0].keys()
		patTemplate = "(.*\\b)%s(\\b.*)"
		ret = expr
		if dictName is None:
			dictName = self._dictSubName
		for kk in keys:
			pat = patTemplate % kk
			mtch = re.match(pat, ret)
			if mtch:
				ret = mtch.groups()[0] + "%s['%s']" % (dictName, kk) + mtch.groups()[1]
		return ret
		
	
	def processFields(self, fields, aliasDict):
		if isinstance(fields, basestring):
			fields = fields.split(",")
		for num, fld in enumerate(fields):
			fld = fld.replace(" AS ", " as ").replace(" As ", " as ").strip()
			fa = fld.split(" as ")
			if len(fa) > 1:
				# An alias is specified
				fld = fa[0].strip()
				aliasDict[fld] = fa[1].strip()
			fields[num] = fld
		return fields, aliasDict


	def select(self, fields=None, where=None, orderBy=None):
		fldList = []
		fldAliases = {}
		whereList = []
		orderByList = []
		keys = self[0].keys()
		if fields is None or fields == "*":
			# All fields
			fields = keys
		fields, fldAliases = self.processFields(fields, fldAliases)
		for fld in fields:
			fldList.append("'%s' : %s" % (fld, self._fldReplace(fld)))
		fieldsToReturn = ", ".join(fldList)
		fieldsToReturn = "{%s}" % fieldsToReturn
		
		# Where list elements
		if where is None:
			whereClause = ""
		else:
			if isinstance(where, basestring):
				where = [where]
			for wh in where:
				whereList.append(self._fldReplace(wh))
			whereClause = " and ".join(whereList)
		if whereClause:
			whereClause = " if %s" % whereClause		
		stmnt = "[%s for %s in self %s]" % (fieldsToReturn, self._dictSubName, whereClause)
		resultSet = eval(stmnt)
		
		if fldAliases:
			# We need to replace the keys for the field names with the 
			# appropriate alias names
			for rec in resultSet:
				for key, val in fldAliases.items():
					orig = rec.get(key)
					if orig:
						rec[val] = orig
						del rec[key]
					
		if orderBy:
			# This should be a comma separated string in the format:
			#		fld1, fld2 desc, fld3 asc
			# After the field name is an optional direction, either 'asc' 
			# (ascending, default) or 'desc' (descending).
			# IMPORTANT! Fields referenced in 'orderBy' MUST be in 
			# the result data set!
			orderByList = orderBy.split(",")
			sortList = []
			
			def orderBySort(val1, val2):
				ret = 0
				compList = orderByList[:]
				while not ret:
					comp = compList[0]
					compList = compList[1:]
					if comp[-4:].lower() == "desc":
						compVals = (-1, 1)
					else:
						compVals = (1, -1)
					# Remove the direction, if any, from the comparison.
					compWords = comp.split(" ")
					if compWords[-1].lower() in ("asc", "desc"):
						compWords = compWords[:-1]
					comp = " ".join(compWords)
					cmp1 = self._fldReplace(comp, "val1")
					cmp2 = self._fldReplace(comp, "val2")
					eval1 = eval(cmp1)
					eval2 = eval(cmp2)
					if eval1 > eval2:
						ret = compVals[0]
					elif eval1 < eval2:
						ret = compVals[1]
					else:
						# They are equal. Continue comparing using the 
						# remaining terms in compList, if any.
						if not compList:
							break
				return ret
		
			resultSet.sort(orderBySort)
		
		return DataSet(resultSet)


	def join(self, target, sourceAlias, targetAlias, condition,
			sourceFields=None, targetFields=None, where=None, 
			orderBy=None, joinType=None):
		"""This method joins the current DataSet and the target 
		DataSet, based on the specified condition. The 'joinType'
		parameter will determine the type of join (inner, left, right, full).
		Where and orderBy will affect the result of the join, and so they
		should reference fields in the result set without alias qualifiers.		
		"""
		if joinType is None:
			joinType = "inner"
		joinType = joinType.lower().strip()
		if joinType == "outer":
			# This is the same as 'left outer'
			joinType = "left"
		if "outer" in joinType.split():
			tmp = joinType.split()
			tmp.remove("outer")
			joinType = tmp[0]
		
		leftDS = self
		rightDS = target
		leftAlias = sourceAlias
		rightAlias = targetAlias
		leftFields = sourceFields
		rightFields = targetFields
		leftFldAliases = {}
		rightFldAliases = {}
		if joinType == "right":
			# Same as left; we just need to reverse things
			(leftDS, rightDS, leftAlias, rightAlias, leftFields, 
					rightFields) = (rightDS, leftDS, rightAlias, leftAlias, 
					rightFields, leftFields)
		
		
		leftFields, leftFldAliases = self.processFields(leftFields, leftFldAliases)
		rightFields, rightFldAliases = self.processFields(rightFields, rightFldAliases)

		# Parse the condition. It should have an '==' in it. If not, 
		# raise an error.
		condList = condition.split("==")
		if len(condList) == 1:
			# No equality specified
			errMsg = _("Bad join: no '==' in join condition: %s") % condition
			raise dException.QueryException, errMsg
		
		leftCond = None
		rightCond = None
		leftPat = "(.*)(\\b%s\\b)(.*)" % leftAlias
		rightPat = "(.*)(\\b%s\\b)(.*)" % rightAlias
		
		mtch = re.match(leftPat, condList[0])
		if mtch:
			leftCond = condList[0].strip()
		else:
			mtch = re.match(leftPat, condList[1])
			if mtch:
				leftCond = condList[1].strip()
		mtch = re.match(rightPat, condList[0])
		if mtch:
			rightCond = condList[0].strip()
		else:
			mtch = re.match(rightPat, condList[1])
			if mtch:
				rightCond = condList[1].strip()
		condError = ""
		if leftCond is None:
			condError += _("No join condition specified for alias '%s'") % leftAlias
		if rightCond is None:
			if condError:
				condError += "; "
			condError += _("No join condition specified for alias '%s'") % rightAlias
		if condError:
			raise dException.QueryException, condError
		
		# OK, we now know how to do the join. The plan is this:
		# 	create an empty result list
		# 	scan through all the left records
		# 		if leftFields, run a select to get only those fields.
		# 		find all the matching right records using select
		# 		if matches, update each with the left select and add
		# 				to the result.
		# 		if no matches:
		# 			if inner join:
		# 				skip to next
		# 			else:
		# 				get dict.fromkeys() for right select
		# 				update left with fromkeys and add to result
		# 	
		# 	We'll worry about full joins later.

		resultSet = []
		for leftRec in leftDS:
			if leftFields:
				leftSelect = DataSet([leftRec]).select(fields=leftFields)[0]
			else:
				leftSelect = leftRec
			tmpLeftCond = leftCond.replace(leftAlias, "leftRec")
			tmpLeftCond = "%s['%s']" % tuple(tmpLeftCond.split("."))
			leftVal = eval(tmpLeftCond)
			
			if isinstance(leftVal, basestring):
				leftVal = "'%s'" % leftVal
			rightWhere = rightCond.replace(rightAlias + ".", "") + "== %s" % leftVal
			rightRecs = rightDS.select(fields=rightFields, where=rightWhere)

			if rightRecs:
				for rightRec in rightRecs:
					rightRec.update(leftSelect)
					resultSet.append(rightRec)
			else:
				if not joinType == "inner":
					rightKeys = rightDS.select(fields=rightFields)[0].keys()
					leftSelect.update(dict.fromkeys(rightKeys))
					resultSet.append(leftSelect)
		
		resultSet = DataSet(resultSet)
		if where or orderBy:
			resultSet = resultSet.select(where=where, orderBy=orderBy)
		return resultSet



class DataSet(tuple):
	""" This class assumes that its contents are not ordinary tuples, but
	rather tuples consisting of dicts, where the dict keys are field names.
	This is the data structure returned by the dCursorMixin class.
	
	It is used to give these data sets the ability to be queried, joined, etc.
	This is accomplished by using SQLite in-memory databases. If SQLite
	and pysqlite2 are not installed on the machine this is run on, a 
	warning message will be printed out and the SQL functions will return 
	None. The data will still be usable, though.
	"""
	def __init__(self, *args, **kwargs):
		super(DataSet, self).__init__(*args, **kwargs)
		if _useSQLite:
			self._connection = None
			self._cursor = None
			self._populated = False
			# We may need to encode fields that are not legal names.
			self.fieldAliases = {}
			# Pickling mementos is slow. This dict will hold them
			# instead
			self._mementoHold = {}
			self._mementoSequence = 0
			# Register the adapters
			sqlite.register_adapter(dMemento, self._adapt_memento)
			if _USE_DECIMAL:
				sqlite.register_adapter(Decimal, self._adapt_decimal)
			
			# Register the converters
			sqlite.register_converter("memento", self._convert_memento)
			if _USE_DECIMAL:
				sqlite.register_converter("decimal", self._convert_decimal)
		
			self._typeDict = {int: "integer", long: "integer", str: "text", 
					unicode: "text", float: "real", datetime.date: "date", 
					datetime.datetime: "timestamp", dMemento : "memento"}
			if _USE_DECIMAL:
				self._typeDict[Decimal] = "decimal"

	
	def __del__(self):
		if _useSQLite:
			if self._cursor is not None:
				self._cursor.close()
			if self._connection is not None:
				self._connection.close()

	
	def _adapt_decimal(self, decVal):
		"""Converts the decimal value to a string for storage"""
		return str(decVal)
	
	
	def _convert_decimal(self, strval):
		"""This is a converter routine. Takes the string 
		representation of a Decimal value and return an actual 
		decimal, if that module is present. If not, returns a float.
		"""
		if _USE_DECIMAL:
			ret = Decimal(strval)
		else:
			ret = float(strval)
		return ret
	
	
	def _adapt_memento(self, mem):
		"""Substitutes a sequence for the memento for storage"""
		pos = self._mementoSequence
		self._mementoSequence += 1
		self._mementoHold[pos] = mem
		return str(pos)
	
	
	def _convert_memento(self, strval):
		"""Replaces the placeholder sequence with the actual memento."""
		pos = int(strval)
		return self._mementoHold[pos]
	
	
	def replace(self, field, valOrExpr, scope=None):
		"""Replaces the value of the specified field with the given value
		or expression. All records matching the scope are affected; if
		no scope is specified, all records are affected.
		
		'valOrExpr' will be treated as a literal value, unless it is prefixed
		with an equals sign. All expressions will therefore be a string 
		beginning with '='. Literals can be of any type. 
		"""
		if scope is None:
			scope = "True"
		else:
			scope = self._fldReplace(scope, "rec")
		
		literal = True
		if isinstance(valOrExpr, basestring):
			if valOrExpr.strip()[0] == "=":
				literal = False
				valOrExpr = valOrExpr.replace("=", "", 1)
			valOrExpr = self._fldReplace(valOrExpr, "rec")
		for rec in self:
			if eval(scope):
				if literal:
					rec[field] = valOrExpr
				else:
					expr = "rec['%s'] = %s" % (field, valOrExpr)
					exec(expr)
		
	
	def sort(self, col, ascdesc=None, caseSensitive=None):
		if ascdesc is None:
			ascdesc = "ASC"
		casecollate = ""
		if caseSensitive is False:
			# The default of None will be case-sensitive
			casecollate = " COLLATE NOCASE "		
		stmnt = "select * from dataset order by %s %s %s"
		stmnt = stmnt % (col, casecollate, ascdesc)
		ret = self.execute(stmnt)
		return ret
		

	def _fldReplace(self, expr, dictName=None):
		"""The list comprehensions require the field names be the keys
		in a dictionary expression. Users, though, should not have to know
		about this. This takes a user-defined, SQL-like expressions, and 
		substitutes any field name with the corresponding dict
		expression.
		"""
		keys = self[0].keys()
		patTemplate = "(.*\\b)%s(\\b.*)"
		ret = expr
		if dictName is None:
			dictName = self._dictSubName
		for kk in keys:
			pat = patTemplate % kk
			mtch = re.match(pat, ret)
			if mtch:
				ret = mtch.groups()[0] + "%s['%s']" % (dictName, kk) + mtch.groups()[1]
		return ret
		
	
	def _makeCreateTable(self, ds, alias=None):
		"""Makes the CREATE TABLE string needed to represent
		this data set. There must be at least one record in the 
		data set, or we can't get the necessary column info.
		"""
		if len(ds) == 0:
			return None
		if alias is None:
			# Use the default
			alias = "dataset"
		rec = ds[0]
		keys = rec.keys()
		retList = []
		
		for key in keys:
			if key.startswith("dabo-"):
				# This is an internal field
				safekey = key.replace("-", "_")
				self.fieldAliases[safekey] = key
			else:
				safekey = key
			typ = type(rec[key])
			try:
				retList.append("%s %s" % (safekey, ds._typeDict[typ]))
			except KeyError:
				retList.append(safekey)
		return "create table %s (%s)" % (alias, ", ".join(retList))
		
	
	def _populate(self, ds, alias=None):
		"""This is the method that converts a Python dataset
		into a SQLite table with the name specified by 'alias'.
		"""
		if alias is None:
			# Use the default
			alias = "dataset"
		if len(ds) == 0:
			# Can't create and populate a table without a structure
			dabo.errorLog.write(_("Cannot populate without data for alias %s") 
					% alias)
			return None
		if ds._populated:
			# Data's already there; no need to re-load it
			return
		self._cursor.execute(self._makeCreateTable(ds, alias))
		
		flds, vals = ds[0].keys(), ds[0].values()
		# Fields may contain illegal names. This will correct them
		flds = [fld.replace("dabo-", "dabo_") for fld in flds]
		fldParams = [":%s" % fld for fld in flds]
		fldCnt = len(flds)
		insStmnt = "insert into %s (%s) values (%s)" % (alias, 
				", ".join(flds), ", ".join(fldParams))
		
		def recGenerator(ds):
			for rec in ds:
				yield rec

		self._cursor.executemany(insStmnt, recGenerator(ds))
		if ds is self:
			self._populated = True
			

	def execute(self, sqlExpr, cursorDict=None):
		"""This method allows you to work with a Python data set
		(i.e., a tuple of dictionaries) as if it were a SQL database. You
		can run any sort of statement that you can in a normal SQL
		database. It requires that SQLite and pysqlite2 are installed;
		if they aren't, this will return None.
		
		The SQL expression can be any standard SQL expression; however,
		the FROM clause should always be: 'from dataset', since these 
		datasets do not have table names.
		
		If you want to do multi-dataset joins, you need to pass the 
		additional DataSet objects in a dictionary, where the value is the
		DataSet, and the key is the alias used to reference that DataSet
		in your join statement.
		"""
		def dict_factory(cursor, row):
			dd = {}
			for idx, col in enumerate(cursor.description):
				dd[col[0]] = row[idx]
			return dd

		class DictCursor(sqlite.Cursor):
			def __init__(self, *args, **kwargs):
				sqlite.Cursor.__init__(self, *args, **kwargs)
				self.row_factory = dict_factory

		if not _useSQLite:
			dabo.errorLog.write(_("SQLite and pysqlite2 must be installed to use this function"))
			return None
		if self._connection is None:
			self._connection = sqlite.connect(":memory:", 
					detect_types=sqlite.PARSE_DECLTYPES|sqlite.PARSE_COLNAMES,
					isolation_level="EXCLUSIVE")
		if self._cursor is None:
			self._cursor = self._connection.cursor(factory=DictCursor)
		
# 		import time
# 		st = time.clock()
# 		print "starting"

		# Create the table for this DataSet
		self._populate(self, "dataset")
		
# 		pt = time.clock()
# 		print "POPULATED", pt-st
		# Now create any of the tables for the join DataSets
		if cursorDict is not None:
			for alias, ds in cursorDict.items():
				self._populate(ds, alias)
				
		# We have a table now with the necessary data. Run the query!
		self._cursor.execute(sqlExpr)
		
# 		et = time.clock()
# 		print "EXECUTED", et - pt
		# We need to know what sort of statement was run. Only a 'select'
		# will return results. The rest ('update', 'delete', 'insert') return
		# nothing. In those cases, we need to run a 'select *' to get the 
		# modified data set.
		if not sqlExpr.lower().strip().startswith("select "):
			self._cursor.execute("select * from dataset")
		tmpres = self._cursor.fetchall()
		
# 		ft = time.clock()
# 		print "FETCH", ft-et
		return DataSet(tmpres)
		
# 		
# 		dabo.trace()
# 		
# 		res = []
# 		if tmpres:
# 			# There will be no description if there are no records.
# 			dscrp = [fld[0] for fld in self._cursor.description]
# 			for tmprec in tmpres:
# 				rec = {}
# 				for pos, val in enumerate(tmprec):
# 					fld = dscrp[pos]
# 					if self.fieldAliases.has_key(fld):
# 						fld = self.fieldAliases[fld]
# 					rec[fld] = val
# 				res.append(rec)
# 		
# 		dt = time.clock()
# 		print "CONVERTED", dt-ft
		






