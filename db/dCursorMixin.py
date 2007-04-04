# dabo/db/dCursorMixin

import types
import datetime
import inspect
import random
import sys
import re
import array
# Make sure that the user's installation supports Decimal.
_USE_DECIMAL = True
try:
	from decimal import Decimal
except ImportError:
	_USE_DECIMAL = False

import dabo
import dabo.dConstants as kons
from dabo.dLocalize import _
import dabo.dException as dException
from dabo.dObject import dObject
from dNoEscQuoteStr import dNoEscQuoteStr
from dabo.db import dTable
from dabo.db.dDataSet import dDataSet
from dabo.lib import dates


class dCursorMixin(dObject):
	"""Dabo's cursor class, representing the lowest tier."""
	_call_initProperties = False
	def __init__(self, sql="", *args, **kwargs):
		self._convertStrToUnicode = True
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
		self._records = dDataSet()
		# Attribute that holds the current row number
		self.__rownumber = -1

		self._autoPopulatePK = True
		self._autoQuoteNames = True

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
		
		# Reference to the bizobj that 'owns' this cursor, if any,
		self._bizobj = None
		
		# set properties for the SQL Builder functions
		self.clearSQL()
		self.hasSqlBuilder = True
		
		# props for building the auxiliary cursor
		self._cursorFactoryFunc = None
		self._cursorFactoryClass = None

		# mementos and new records, keyed on record object ids:
		self._mementos = {}
		self._newRecords = {}
		
		# Flag preference cursors so that they don't fill up the logs
		self._isPrefCursor = False

		self.initProperties()


	def setCursorFactory(self, func, cls):
		self._cursorFactoryFunc = func
		self._cursorFactoryClass = cls
		
	
	def clearSQL(self):
		self._fieldClause = ""
		self._fromClause = ""
		self._joinClause = ""
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
	
	
	def pkExpression(self, rec=None):
		"""Returns the PK expression for the passed record."""
		if rec is None:
			rec = self._records[self.RowNumber]
		if isinstance(self.KeyField, tuple):
			pk = tuple([rec[kk] for kk in self.KeyField])
		else:
			pk = rec[self.KeyField]
		return pk
		

	def _correctFieldType(self, field_val, field_name, _fromRequery=False):
		"""Correct the type of the passed field_val, based on self.DataStructure.

		This is called by self.execute(), and contains code to convert all strings 
		to unicode, as well as to correct any datatypes that don't match what 
		self.DataStructure reports. The latter can happen with SQLite, for example,
		which only knows about a quite limited number of types.
		"""
		ret = field_val
		showError = False
		if _fromRequery:
			pythonType = self._types.get(field_name, type(field_val))
			daboType = dabo.db.getDaboType(pythonType)

			if pythonType in (type(None), None) or isinstance(field_val, pythonType):
				# No conversion needed.
				return ret

			if pythonType in (unicode,):
				# Unicode conversion happens below.
				pass
			elif field_val is None:
				# Fields of any type can be None (NULL).
				return field_val
			elif pythonType in (datetime.datetime, ) and isinstance(field_val, basestring):
				ret = dates.getDateTimeFromString(field_val)
				if ret is None:
					ret = field_val
				else:
					return ret
			elif pythonType in (datetime.date,) and isinstance(field_val, basestring):
				ret = dates.getDateFromString(field_val)
				if ret is None:
					ret = field_val
				else:
					return ret
			elif _USE_DECIMAL and pythonType in (Decimal,):
				ds = self.DataStructure
				ret = None
				_field_val = field_val
				if type(field_val) in (float,):
					# Can't convert to decimal directly from float
					_field_val = str(_field_val)
				# Need to convert to the correct scale:
				scale = None
				for s in ds:
					if s[0] == field_name:
						if len(s) > 5:
							scale = s[5]
				if scale is None:
					scale = 2
				return Decimal(_field_val).quantize(Decimal("0.%s" % (scale * "0",)))
			else:
				try:
					return pythonType(field_val)
				except Exception, e:
					pass

		# Do the unicode conversion last:
		if isinstance(field_val, str) and self._convertStrToUnicode:
			try:
				return unicode(field_val, self.Encoding)
			except UnicodeDecodeError, e:
				# Try some common encodings:
				ok = False
				for enc in ("utf-8", "latin-1", "iso-8859-1"):
					if enc != self.Encoding:
						try:
							ret = unicode(field_val, enc)
							ok = True
						except UnicodeDecodeError:
							continue
						if ok:
							# change self.Encoding and log the message
							self.Encoding = enc
							dabo.errorLog.write(_("Field %(fname)s: Incorrect unicode encoding set; using '%(enc)s' instead")
								% {'fname':field_name, 'enc':enc} )
							return ret
							break
				else:
					raise UnicodeDecodeError, e
# 		elif isinstance(field_val, array.array):
# 			# Usually blob data
# 			ret = field_val.tostring()

			dabo.errorLog.write(_("%s couldn't be converted to %s (field %s)") 
					% (repr(field_val), pythonType, field_name))
		return ret


	def execute(self, sql, params=(), _fromRequery=False):
		""" Execute the sql, and populate the DataSet if it is a select statement."""
		# The idea here is to let the super class do the actual work in 
		# retrieving the data. However, many cursor classes can only return 
		# row information as a list, not as a dictionary. This method will 
		# detect that, and convert the results to a dictionary.

		#### NOTE: NEEDS TO BE TESTED THOROUGHLY!!!!  ####

		# Some backends, notably Firebird, require that fields be specially marked.
		if not isinstance(sql, unicode):
			sql = unicode(sql, self.Encoding)
		sql = self.processFields(sql)
		
		try:
			if params is None or len(params) == 0:
				res = self.superCursor.execute(self, sql)
				if not self.IsPrefCursor:
					dabo.dbActivityLog.write("SQL: %s" % sql.replace("\n", " "))
			else:
				res = self.superCursor.execute(self, sql, params)
				if not self.IsPrefCursor:
					dabo.dbActivityLog.write("SQL: %s, PARAMS: %s" % (sql.replace("\n", " "), ", ".join(params)))
		except Exception, e:
			dabo.dbActivityLog.write("FAILED SQL: %s, PARAMS: %s" % (sql.replace("\n", " "), ", ".join(params)))
			# If this is due to a broken connection, let the user know.
			# Different backends have different messages, but they
			# should all contain the string 'connect' in them.
			if "connect" in str(e).lower():
				raise dException.ConnectionLostException, e
			if "access" in str(e).lower():
				raise dException.DBNoAccessException(e)
			else:
				raise dException.DBQueryException(e, sql)

		# Some backend programs do odd things to the description
		# This allows each backend to handle these quirks individually.
		self.BackendObject.massageDescription(self)

		if _fromRequery:
			self._storeFieldTypes()

		if sql.strip().split()[0].lower() not in  ("select", "pragma"):
			# No need to massage the data for DML commands
			self._records = dDataSet(tuple())
			return res

		try:
			_records = self.fetchall()
		except Exception, e:
			_records = tuple()
			dabo.errorLog.write("Error fetching records: %s" % e)

		if _records and not self.BackendObject._alreadyCorrectedFieldTypes:
			if isinstance(_records[0], (tuple, list)):
				# Need to convert each row to a Dict, since the backend didn't do it.
				tmpRows = []
				fldNames = [f[0] for f in self.FieldDescription]
				for row in _records:
					dic = {}
					for idx, fldName in enumerate(fldNames):
						dic[fldName] = self._correctFieldType(field_val=row[idx], 
								field_name=fldName, _fromRequery=_fromRequery)
					tmpRows.append(dic)
				_records = tmpRows
			else:
				# Already a DictCursor, but we still need to correct the field types.
				for row in _records:
					for fld, val in row.items():
						row[fld] = self._correctFieldType(field_val=val, field_name=fld,
								_fromRequery=_fromRequery)

		self._records = dDataSet(_records)

		if self.RowCount > 0:
			self.RowNumber = max(0, self.RowNumber)
			maxrow = max(0, (self.RowCount-1) )
			self.RowNumber = min(self.RowNumber, maxrow)

		return res


	def executeSafe(self, sql):
		"""Execute the passed SQL using an auxiliary cursor.

		This is considered 'safe', because it won't harm the contents of the
		main cursor.
		"""
		return self.AuxCursor.execute(sql)

	
	def requery(self, params=None):
		self._lastSQL = self.CurrentSQL
		self.lastParams = params
		self._savedStructureDescription = []

		self.execute(self.CurrentSQL, params, _fromRequery=True)
		
		# clear mementos and new record flags:
		self._mementos = {}
		self._newRecords = {}

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


	def _storeFieldTypes(self, target=None):
		"""Stores the data type for each column in the result set."""
		if target is None:
			target = self
		target._types = {}
		for field in self.DataStructure:
			field_alias, field_type = field[0], field[1]
			target._types[field_alias] = dabo.db.getPythonType(field_type)

	
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
		if not self._records[0].has_key(col) and not self.VirtualFields.has_key(col):
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
		if not kf:
			return
			
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
			for row, rec in enumerate(self._records):
				sortList.append([self.getFieldVal(col, row), rec])
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
		self._records = dDataSet(newRows)

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
					for k,v in rec.items() ]
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
		return list(set(self.nonUpdateFields + self.__nonUpdateFields))
		
		
	def __setNonUpdateFields(self):
		"""Automatically set the non-update fields."""
		dataStructure = getattr(self, "_dataStructure", None)
		if dataStructure is not None:
			# Use the explicitly-set DataStructure to find the NonUpdateFields.
			nonUpdateFieldAliases = []
			for field in dataStructure:
				field_alias = field[0]
				table_name = field[3]
				if table_name != self.Table:
					nonUpdateFieldAliases.append(field_alias)
			self.__nonUpdateFields = nonUpdateFieldAliases
		else:
			# Delegate to the backend object to figure it out.
			self.BackendObject.setNonUpdateFields(self)
	

	def isChanged(self, allRows=True):
		"""Return True if there are any changes to the local field values.

		If allRows is True (the default), all records in the recordset will be 
		considered. Otherwise, only the current record will be checked.
		"""
		if allRows:
			#return len(self._mementos) > 0 or len(self._newRecords) > 0
			return len(self._mementos) > 0
		else:
			row = self.RowNumber

			try:
				rec = self._records[row]
			except IndexError:
				# self.RowNumber doesn't exist (init phase?) Nothing's changed:
				return False
			recKey = self.pkExpression(rec)
			memento = self._mementos.get(recKey, None)
			#new_rec = self._newRecords.has_key(recKey)
			#return not (memento is None and not new_rec)
			return not (not memento)


	def setNewFlag(self):
		"""Set the current record to be flagged as a new record.

		dBizobj will automatically call this method as appropriate, but if you are
		using dCursor without a proxy dBizobj, you'll need to manually call this 
		method after cursor.new(), and (if applicable) after cursor.genTempAutoPK().
		For example:
			cursor.new()
			cursor.genTempAutoPK()
			cursor.setNewFlag()
		"""	
		if self.KeyField:
			rec = self._records[self.RowNumber]
			self._newRecords[rec[self.KeyField]] = None


	def genTempAutoPK(self):
		""" Create a temporary PK for a new record. Set the key field to this
		value, and also create a temp field to hold it so that when saving the
		new record, child records that are linked to this one can be updated
		with the actual PK value.
		"""
		rec = self._records[self.RowNumber]
		kf = self.KeyField
		try:
			if isinstance(kf, tuple):
				pkVal = rec[kf[0]]
			else:
				pkVal = rec[kf]
		except IndexError:
			# No records; default to string
			pkVal = ""
		
		tmpPK = self._genTempPKVal(pkVal)
		if isinstance(kf, tuple):
			for key in kf:
				rec[key] = tmpPK
		else:
			rec[kf] = tmpPK
		rec[kons.CURSOR_TMPKEY_FIELD] = tmpPK
		return tmpPK
		
	
	def _genTempPKVal(self, pkValue):
		""" Return the next available temp PK value. It will be a string, and 
		postfixed with '-dabotmp' to avoid potential conflicts with actual PKs
		"""
		ret = self.__tmpPK
		# Decrement the temp PK value
		self.__tmpPK -= 1
		if isinstance(pkValue, basestring):
			ret = "%s-dabotmp" % ret
		return ret
	
	
	def getPK(self):
		""" Returns the value of the PK field in the current record. If that record
		is new an unsaved record, return the temp PK value. If this is a compound 
		PK, return a tuple containing each field's values.
		"""
		ret = None
		if self.RowCount <= 0:
			raise dException.NoRecordsException, _("No records in the data set.")
		rec = self._records[self.RowNumber]
		recKey = self.pkExpression()
		if self._newRecords.has_key(recKey) and self.AutoPopulatePK:
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
		if self.RowCount <= 0:
			raise dException.NoRecordsException, _("No records in the data set.")
		if row is None:
			row = self.RowNumber

		rec = self._records[row]
		if isinstance(fld, (tuple, list)):
			ret = []
			for xFld in fld:
				ret.append(self.getFieldVal(xFld, row=row))
			return tuple(ret)
		else:
			if rec.has_key(fld):
				return rec[fld]
			else:
				if self.VirtualFields.has_key(fld):
					# Move to specified row if necessary, and then call the VirtualFields
					# function, which expects to be on the correct row.
					_oldrow = self.RowNumber
					self.RowNumber = row
					ret = self.VirtualFields[fld]()
					self.RowNumber = _oldrow
					return ret
				else:
					raise dException.FieldNotFoundException, "%s '%s' %s" % (
							_("Field"), fld, _("does not exist in the data set"))


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
				ret = {"C": unicode, "D": datetime.date, "B": bool, "G": long,
					"N": float, "M": unicode, "I": int, "T": datetime.datetime}[typ]
			except KeyError:
				ret = None
		return ret
		

	def _hasValidKeyField(self):
		"""Return True if the KeyField exists and names valid fields."""
		try:
			self.checkPK()
		except dException.MissingPKException:
			return False
		return True


	def setFieldVal(self, fld, val, row=None):
		"""Set the value of the specified field."""
		if self.RowCount <= 0:
			raise dException.NoRecordsException, _("No records in the data set")

		if row is None:
			row = self.RowNumber

		rec = self._records[row]
		valid_pk = self._hasValidKeyField()
		keyField = self.KeyField
		if not rec.has_key(fld):
			if self.VirtualFields.has_key(fld):
				# ignore
				return
			ss = _("Field '%s' does not exist in the data set.") % (fld,)
			raise dException.FieldNotFoundException, ss

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
				elif isinstance(val, dNoEscQuoteStr):
					# Sometimes you want to set it to a sql function, equation, ect.
					ignore = True
				elif fld in self.getNonUpdateFields():
					# don't worry so much if this is just a calculated field.
					ignore = True
				else:
					# This can also happen with a new record, since we just stuff the
					# fields full of empty strings.
					ignore = self._newRecords.has_key(rec[keyField])
						
				if not ignore:
					msg = _("!!! Data Type Mismatch: field=%s. Expecting: %s; got: %s") \
							% (fld, str(fldType), str(type(val)))
					dabo.errorLog.write(msg)

		# If the new value is different from the current value, change it and also
		# update the mementos if necessary.
		old_val = rec[fld]
		nonUpdateFields = self.getNonUpdateFields()
		if old_val != val:
			if valid_pk:
				if fld == keyField:
					# Changing the key field value, need to key the mementos on the new
					# value, not the old. Additionally, need to copy the mementos from the
					# old key value to the new one.
					keyFieldValue = val
					old_mem = self._mementos.get(old_val, None)
					if old_mem is not None:
						self._mementos[keyFieldValue] = old_mem
						del self._mementos[old_val]
				else:
					if self._compoundKey:
						keyFieldValue = tuple([rec[k] for k in keyField])
					else:
						keyFieldValue = rec[keyField]
				mem = self._mementos.get(keyFieldValue, {})
				if mem.has_key(fld) or fld in nonUpdateFields:
					# Memento is already there, or it isn't updateable.
					pass
				else:
					# Save the memento for this field.
					mem[fld] = old_val
				if mem.has_key(fld) and mem[fld] == val:
					# Value changed back to the original memento value; delete the memento.
					del mem[fld]
				if mem:
					self._mementos[keyFieldValue] = mem
				else:
					self._clearMemento(row)
			else:
				dabo.infoLog.write("Field value changed, but the memento can't be saved, because there is no valid KeyField.")

			# Finally, save the new value to the field:
			rec[fld] = val


	def getRecordStatus(self, row=None):
		""" Returns a dictionary containing an element for each changed 
		field in the specified record (or the current record if none is specified).
		The field name is the key for each element; the value is a 2-element
		tuple, with the first element being the original value, and the second 
		being the current value.
		"""
		ret = {}
		if row is None:
			row = self.RowNumber

		rec = self._records[row]
		recKey = self.pkExpression(rec)
		mem = self._mementos.get(recKey, {})
	
		for k, v in mem.items():
			ret[k] = (v, rec[k])
		return ret


	def _getNewRecordDiff(self, row=None):
		""" Returns a dictionary containing an element for each field 
		in the specified record (or the current record if none is specified).
		The field name is the key for each element; the value is a 2-element
		tuple, with the first element being the original value, and the second 
		being the current value.

		This is used internally in __saverow, and only applies to new records.
		"""
		ret = {}
		if row is None:
			row = self.RowNumber

		rec = self._records[row]
		for k, v in rec.items():
			if k not in (kons.CURSOR_TMPKEY_FIELD,):
				ret[k] = (None, v)
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
		
		
	def getDataSet(self, flds=(), rowStart=0, rows=None, returnInternals=False):
		""" Get the entire data set encapsulated in a dDataSet object. 

		If the optional	'flds' parameter is given, the result set will be filtered 
		to only include the specified fields. rowStart specifies the starting row
		to include, and rows is the number of rows to return. 
		"""
		ds = []
		internals = (kons.CURSOR_TMPKEY_FIELD,)

		if rows is None:
			rows = self.RowCount
		for row, rec in enumerate(self._records):
			if row >= rowStart and row < (rowStart+rows):
				tmprec = rec.copy()
				for k, v in self.VirtualFields.items():
					tmprec.update({k: self.getFieldVal(k, row)})
				if flds:
					# user specified specific fields - get rid of all others
					for k in tmprec.keys():
						if k not in flds:
							del tmprec[k]
				if not flds and not returnInternals:
					# user didn't specify explicit fields and doesn't want internals
					for internal in internals:
						if tmprec.has_key(internal):
							del tmprec[internal]
				ds.append(tmprec)
		return dDataSet(ds)

	
	def replace(self, field, valOrExpr, scope=None):
		"""Replaces the value of the specified field with the given value
		or expression. All records matching the scope are affected; if
		no scope is specified, all records are affected.
		
		'valOrExpr' will be treated as a literal value, unless it is prefixed
		with an equals sign. All expressions will therefore be a string 
		beginning with '='. Literals can be of any type. 
		"""
		if isinstance(self._records, dDataSet):
			# Make sure that the data set object has any necessary references
			self._records.Cursor = self
			self._records.Bizobj = self._bizobj			
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


	def save(self, allRows=False, useTransaction=False):
		""" Save any changes to the data back to the data store."""
		# Make sure that there is data to save
		if self.RowCount <= 0:
			raise dException.NoRecordsException, _("No data to save")
		# Make sure that there is a PK
		self.checkPK()

		def saverow(row):
			try:
				self.__saverow(row)
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
					raise
	
		if useTransaction:
			self.beginTransaction()

		# Faster to deal with 2 specific cases: all rows or just current row
		if allRows:
			pks_to_save = self._mementos.keys()
			for pk_id in pks_to_save:
				row, rec = self._getRecordByPk(pk_id)
				saverow(row)
		else:
			pk = self.pkExpression()
			if pk in self._mementos.keys():
				saverow(self.RowNumber)
		
		if useTransaction:
			self.commitTransaction()


	def __saverow(self, row):
		rec = self._records[row]
		recKey = self.pkExpression(rec)
		newrec = self._newRecords.has_key(recKey)
		if newrec:
			diff = self._getNewRecordDiff(row)
		else:
			diff = self.getRecordStatus(row)
		aq = self.AutoQuoteNames
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
					flds += ", " + self.BackendObject.encloseNames(kk, aq)
					# add value to expression
					vals += ", %s" % (self.formatForQuery(vv[1]),)
					
				# Trim leading comma-space from the strings
				flds = flds[2:]
				vals = vals[2:]
				if not flds:
					# Some backends (sqlite) require non-empty field clauses. We already
					# know that we are expecting the backend to generate the PK, so send
					# NULL as the PK Value:
					flds = self.KeyField
					vals = "NULL"
				sql = "insert into %s (%s) values (%s) " % (
						self.BackendObject.encloseNames(self.Table, aq), flds, vals)

			else:
				pkWhere = self.makePkWhere(row)
				updClause = self.makeUpdClause(diff)
				sql = "update %s set %s where %s" % (self.BackendObject.encloseNames(self.Table, aq), 
						updClause, pkWhere)
			oldPKVal = self.pkExpression(rec)
			newPKVal = None
			if newrec and self.AutoPopulatePK:
				# Some backends do not provide a means to retrieve 
				# auto-generated PKs; for those, we need to create the 
				# PK before inserting the record so that we can pass it on
				# to any linked child records. NOTE: if you are using 
				# compound PKs, this cannot be done.
				newPKVal = self.pregenPK()
				if newPKVal and not self._compoundKey:
					self.setFieldVal(self.KeyField, newPKVal, row)
			
			#run the update
			aux = self.AuxCursor
			res = aux.execute(sql)

			if newrec and self.AutoPopulatePK and (newPKVal is None):
				# Call the database backend-specific code to retrieve the
				# most recently generated PK value.
				newPKVal = aux.getLastInsertID()
				if newPKVal and not self._compoundKey:
					self.setFieldVal(self.KeyField, newPKVal, row)

			self._clearMemento(row)
			if newrec:
				self._clearNewRecord(row=row, pkVal=oldPKVal)
			else:
				if not res:
					# Different backends may cause res to be None
					# even if the save is successful.
					self.BackendObject.noResultsOnSave()


	def _clearMemento(self, row=None):
		"""Erase the memento for the passed row, or current row if none passed."""
		if row is None:
			row = self.RowNumber
		rec = self._records[row]

		try:
			del self._mementos[rec[self.KeyField]]
		except KeyError:
			# didn't exist
			pass


	def _clearNewRecord(self, row=None, pkVal=None):
		"""Erase the new record flag for the passed row, or current row if none passed."""

		# If pkVal passed, delete that reference:
		if pkVal is not None:
			try:
				del self._newRecords[pkVal]
				if row is None:
					# We deleted based on pk, don't delete flag for the current row.
					return				
			except:
				pass

		if row is None:
			row = self.RowNumber
		rec = self._records[row]

		try:
			del self._newRecords[rec[self.KeyField]]
		except KeyError:
			# didn't exist
			pass


	def pregenPK(self):
		"""Various backend databases require that you manually 
		generate new PKs if you need to refer to their values afterward.
		This method will call the backend to generate and 
		retrieve a new PK if the backend supports this. We use the 
		auxiliary cursor so as not to alter the current data.
		"""
		return self.BackendObject.pregenPK(self.AuxCursor)
		
		
	def new(self):
		"""Add a new record to the data set."""
		if not self._blank:
			self.__setStructure()
		blank = self._blank.copy()
		self._records += dDataSet((blank,))
		# Adjust the RowCount and position
		self.RowNumber = self.RowCount - 1


	def cancel(self, allRows=False):
		""" Revert any changes to the data set back to the original values."""
		if not self.RowCount > 0:
			raise dException.NoRecordsException, _("No data to cancel.")

		# Faster to deal with 2 specific cases: all rows or just current row
		if allRows:
			recs = self._records

			if self._newRecords:
				recs = list(recs)
				delrecs_ids = self._newRecords.keys()
				delrecs_idx = []
				for rec_id in delrecs_ids:
					# Remove any memento associated with the canceled new record, and 
					# append to the list of indexes to delete.
					row, rec = self._getRecordByPk(rec_id)
					self._clearMemento(row)
					delrecs_idx.append(self._records._index(rec))
				delrecs_idx.sort(reverse=True)
				for idx in delrecs_idx:
					del recs[idx]
				self._newRecords = {}
				recs = dDataSet(recs)
				if self.RowNumber >= self.RowCount:
					self.RowNumber = self.RowCount - 1

			for rec_pk, mem in self._mementos.items():
				row, rec = self._getRecordByPk(rec_pk)
				for fld, val in mem.items():
					self._records[row][fld] = val
			self._mementos = {}
		
		else:
			row = self.RowNumber
			rec = self._records[row]
			recKey = self.pkExpression(rec)
			if self._newRecords.has_key(recKey):
				# We simply need to remove the row, and clear the memento and newrec flag.
				self._clearMemento(row)
				self._clearNewRecord(row)
				recs = list(self._records)
				del recs[recs.index(rec)]
				self._records = dDataSet(recs)
				if self.RowNumber >= self.RowCount:
					self.RowNumber = self.RowCount - 1
				return
			
			# Not a new record: need to manually replace the old values:
			for fld, val in self._mementos.get(recKey, {}).items():
				self._records[row][fld] = val
			self._clearMemento(row)
			
	
	def delete(self, delRowNum=None):
		"""Delete the specified row, or the currently active row."""
		if self.RowNumber < 0 or self.RowCount == 0:
			# No query has been run yet
			raise dException.NoRecordsException, _("No record to delete")
		if delRowNum is None:
			# assume that it is the current row that is to be deleted
			delRowNum = self.RowNumber

		rec = self._records[delRowNum]
		pk = self.pkExpression(rec)
		if self._newRecords.has_key(pk):
			res = True
			del self._newRecords[pk]
			if self._mementos.has_key(pk):
				del self._mementos[pk]
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
			self._removeRow(delRowNum)
	
	
	def _removeRow(self, row):
		## Since record sets are tuples and thus immutable, we need to do this 
		## little dance to remove a row.
		lRec = list(self._records)
		del lRec[row]
		self._records = dDataSet(lRec)
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
		rec = self._records[self.RowNumber]
		keyField = self.KeyField
		keyFieldSet = False

		def setDefault(field, val):
			if rec.has_key(field):
				# If it is a function, execute it to get the value, else use literal.
				if callable(val):
					val = val()
				elif isinstance(val, tuple) and val and callable(val[0]):
					# This is a tuple consisting of a function and zero to many parameters
					fnc = val[0]
					prms = val[1:]
					val = fnc(*prms)
				self.setFieldVal(field, val)
			else:
				raise dException.FieldNotFoundException, _("Can't set default value for nonexistent field '%s'.") % field

		if keyField in vals.keys():
			# Must set the pk default value first, for mementos to be filled in
			# correctly.
			setDefault(keyField, vals[keyField])
			keyFieldSet = True
			
		for field, val in vals.items():
			if field == keyField and keyFieldSet:
				continue
			setDefault(field, val)


	def __setStructure(self):
		"""Set the structure of a newly-added record."""
		for field in self.DataStructure:
			field_alias = field[0]
			field_type = field[1]
			field_ispk = field[2]
			table_name = field[3]
			field_name = field[4]
			field_scale = field[5]

			typ = dabo.db.getPythonType(field_type)
			# Handle the non-standard cases
			if _USE_DECIMAL and typ is Decimal:
				newval = Decimal()
				# If the backend reports a decimal scale, use it. Scale refers to the
				# number of decimal places.
				scale = field_scale
				if scale is None:
					scale = 2
				ex = "0.%s" % ("0"*scale)
				newval = newval.quantize(Decimal(ex))
			elif typ is datetime.datetime:
				newval = datetime.datetime.min
			elif typ is datetime.date:
				newval = datetime.date.min
			elif typ is None:
				newval = None
			else:
				try:
					newval = typ()
				except Exception, e:
					dabo.errorLog.write(_("Failed to create newval for field '%s'") % field_alias)
					dabo.errorLog.write(str(e))
					newval = u""

			self._blank[field_alias] = newval

		# Mark the calculated and derived fields.
		self.__setNonUpdateFields()


	def getChangedRows(self):
		"""Returns a list of rows with changes."""
		return map(self._getRowByPk, self._mementos.keys())
		

	def _getRecordByPk(self, pk):
		"""Find the record with the passed primary key; return (row, record)."""
		for idx, rec in enumerate(self._records):
			if self._compoundKey:
				key = tuple([rec[k] for k in self.KeyField])
			else:
				key = rec[self.KeyField]
			if key == pk:
				return (idx, rec)
		return (None, None)


	def _getRowByPk(self, pk):
		"""Find the record with the passed primary key value; return row number."""
		row, rec = self._getRecordByPk(pk)
		return row


	def moveToPK(self, pk):
		""" Find the record with the passed primary key, and make it active.

		If the record is not found, the position is set to the first record. 
		"""
		row, rec = self._getRecordByPk(pk)
		if row is None:
			row = 0
		self.RowNumber = row


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
			raise dException.MissingPKException, _("checkPK failed; no primary key specified")

		if isinstance(kf, basestring):
			kf = [kf]
		# Make sure that there is a field with that name in the data set
		try:
			for fld in kf:
				self._records[0][fld]
		except:
			raise dException.MissingPKException, _("Primary key field does not exist in the data set: ") + fld


	def makePkWhere(self, row=None):
		""" Create the WHERE clause used for updates, based on the pk field. 

		Optionally pass in a row number, otherwise use the current record.
		"""
		bo = self.BackendObject
		tblPrefix = bo.getWhereTablePrefix(self.Table, 
					autoQuote=self.AutoQuoteNames)
		if not row:
			row = self.RowNumber
		rec = self._records[row]
		
		if self._compoundKey:
			keyFields = [fld for fld in self.KeyField]
		else:
			keyFields = [self.KeyField]
		recKey = self.pkExpression(rec)
		mem = self._mementos.get(recKey, {})

		def getPkVal(fld):
			if mem.has_key(fld):
				return mem[fld]
			else:
				return rec[fld]
			
		ret = ""
		for fld in keyFields:
			fldSafe = bo.encloseNames(fld, self.AutoQuoteNames)
			if ret:
				ret += " AND "
			pkVal = getPkVal(fld)
			if isinstance(pkVal, basestring):
				ret += tblPrefix + fldSafe + "='" + pkVal.encode(self.Encoding) + "' "
			elif isinstance(pkVal, (datetime.date, datetime.datetime)):
				ret += tblPrefix + fldSafe + "=" + self.formatDateTime(pkVal) + " "
			else:
				ret += tblPrefix + fldSafe + "=" + str(pkVal) + " "
		return ret


	def makeUpdClause(self, diff):
		""" Create the 'set field=val' section of the Update statement. """
		ret = ""
		bo = self.BackendObject
		aq = self.AutoQuoteNames
		tblPrefix = bo.getUpdateTablePrefix(self.Table, autoQuote=aq)
		for fld, val in diff.items():
			old_val, new_val = val
			# Skip the fields that are not to be updated.
			if fld in self.getNonUpdateFields():
				continue
			if ret:
				ret += ", "
			ret += tblPrefix + bo.encloseNames(fld, aq) + " = " + self.formatForQuery(new_val)
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


	def addField(self, exp, alias=None):
		""" Add a field to the field clause."""
		sm = self.sqlManager
		beo = sm.BackendObject
		if beo:
			sm._fieldClause = beo.addField(sm._fieldClause, exp, alias, 
					autoQuote=self.AutoQuoteNames)
		return sm._fieldClause


	def getFromClause(self):
		""" Get the from clause of the sql statement."""
		return self.sqlManager._fromClause


	def setFromClause(self, clause):
		""" Set the from clause of the sql statement."""
		self.sqlManager._fromClause = self.sqlManager.BackendObject.setFromClause(clause, 
					autoQuote=self.AutoQuoteNames)


	def addFrom(self, exp):
		""" Add a table to the sql statement. For joins, use 
		the addJoin() method.
		"""
		if self.sqlManager.BackendObject:
			self.sqlManager._fromClause = self.sqlManager.BackendObject.addFrom(self.sqlManager._fromClause, exp, 
					autoQuote=self.AutoQuoteNames)
		return self.sqlManager._fromClause


	def getJoinClause(self):
		""" Get the join clause of the sql statement."""
		return self.sqlManager._joinClause


	def setJoinClause(self, clause):
		""" Set the join clause of the sql statement."""
		self.sqlManager._joinClause = self.sqlManager.BackendObject.setJoinClause(clause, 
					autoQuote=self.AutoQuoteNames)


	def addJoin(self, tbl, joinCondition, joinType=None):
		""" Add a joined table to the sql statement."""
		if self.sqlManager.BackendObject:
			self.sqlManager._joinClause = self.sqlManager.BackendObject.addJoin(tbl, 
					joinCondition, self.sqlManager._joinClause, joinType, 
					autoQuote=self.AutoQuoteNames)
		return self.sqlManager._joinClause
		


	def getWhereClause(self):
		""" Get the where clause of the sql statement."""
		return self.sqlManager._whereClause


	def setWhereClause(self, clause):
		""" Set the where clause of the sql statement."""
		self.sqlManager._whereClause = self.sqlManager.BackendObject.setWhereClause(clause, 
					autoQuote=self.AutoQuoteNames)


	def addWhere(self, exp, comp="and"):
		""" Add an expression to the where clause."""
		if self.sqlManager.BackendObject:
			self.sqlManager._whereClause = self.sqlManager.BackendObject.addWhere(self.sqlManager._whereClause, exp, comp, 
					autoQuote=self.AutoQuoteNames)
		return self.sqlManager._whereClause


	def prepareWhere(self, clause):
		""" Modifies WHERE clauses as needed for each backend. """
		return self.sqlManager.BackendObject.prepareWhere(clause, 
					autoQuote=self.AutoQuoteNames)
		
		
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
			self.sqlManager._groupByClause = self.sqlManager.BackendObject.addGroupBy(self.sqlManager._groupByClause,
					exp, autoQuote=self.AutoQuoteNames)
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
			self.sqlManager._orderByClause = self.sqlManager.BackendObject.addOrderBy(self.sqlManager._orderByClause, 
					exp, autoQuote=self.AutoQuoteNames)
		return self.sqlManager._orderByClause


	def getLimitClause(self):
		""" Get the limit clause of the sql statement."""
		return self.sqlManager._limitClause
		

	def setLimitClause(self, clause):
		""" Set the limit clause of the sql statement."""
		self.sqlManager._limitClause = clause
	
	# For simplicity's sake, create aliases
	setLimit, getLimit = setLimitClause, getLimitClause



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
		joinClause = self.sqlManager._joinClause
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
			fromClause = "  from " + fromClause
		else:
			fromClause = "  from " + self.sqlManager.Table
		if joinClause:
			joinClause = " " + joinClause
		if whereClause:
			whereClause = " where " + whereClause
		if groupByClause:
			groupByClause = " group by " + groupByClause
		if orderByClause:
			orderByClause = " order by " + orderByClause
		if limitClause:
			limitClause = " %s %s" % (self.sqlManager.getLimitWord(), limitClause)
		elif limitClause is None:
			# The limit clause was specifically disabled.
			limitClause = ""
		else:
			limitClause = " %s %s" % (self.sqlManager.getLimitWord(), self.sqlManager._defaultLimit)

		return self.sqlManager.BackendObject.formSQL(fieldClause, fromClause, joinClause, 
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
		

	def oldVal(self, fieldName, row=None):
		"""Returns the value of the field as it existed after the last requery."""
		if self.RowCount < 1:
			raise dabo.dException.NoRecordsException
		if row is None:
			row = self.RowNumber
		rec = self._records[row]
		pk = self.pkExpression(rec)
		mem = self._mementos.get(pk, None)
		if mem and mem.has_key(fieldName):
			return mem[fieldName]
		return self.getFieldVal(fieldName, row)


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


	def _getAutoQuoteNames(self):
		return self._autoQuoteNames

	def _setAutoQuoteNames(self, val):
		self._autoQuoteNames = val


	def _getAuxCursor(self):
		if self.__auxCursor is None:
			if self._cursorFactoryClass is not None:
				if self._cursorFactoryFunc is not None:
					self.__auxCursor = self._cursorFactoryFunc(self._cursorFactoryClass)
		if not self.__auxCursor:
			self.__auxCursor = self.BackendObject.getCursor(self.__class__)
		self.__auxCursor.BackendObject = self.BackendObject
		return self.__auxCursor
	

	def _getBackendObject(self):
		return self.__backend

	def _setBackendObject(self, obj):
		self.__backend = obj
#		self.AuxCursor.__backend = obj
	
		
	def _getCurrentSQL(self):
		if self.UserSQL is not None:
			return self.UserSQL
		return self.AutoSQL
		

	def _getDescrip(self):
		return self.__backend.getDescription(self)
		

	def _getDataStructure(self):
		val = getattr(self, "_dataStructure", None)
		if val is None:
			# Get the information from the backend. Note that elements 3 and 4 get
			# guessed-at values.
			val = getattr(self, "_savedStructureDescription", [])
			if not val:
				if self.BackendObject is None:
					# Nothing we can do. We are probably an AuxCursor
					pass
				else:
					ds = self.BackendObject.getStructureDescription(self)
					for field in ds:
						field_name, field_type, pk = field[0], field[1], field[2]
						try:
							field_scale = field[5]
						except IndexError:
							field_scale = None
						val.append((field_name, field_type, pk, self.Table, field_name, field_scale))
				self._savedStructureDescription = val
			self._dataStructure = val
		return tuple(val)

	def _setDataStructure(self, val):
		# Go through the sequence, raising exceptions or adding default values as
		# appropriate.
		val = list(val)
		for idx, field in enumerate(val):
			field_alias = field[0]
			field_type = field[1]
			try:
				field_pk = field[2]
			except IndexError:
				field_pk = False
			try:
				table_name = field[3]
			except IndexError:
				table_name = self.Table
			try:
				field_name = field[4]
			except IndexError:
				field_name = field_alias
			try:
				field_scale = field[5]
			except IndexError:
				field_scale = None
			val[idx] = (field_alias, field_type, field_pk, table_name, field_name, field_scale)
		self._dataStructure = tuple(val)

			
	def _getEncoding(self):
		return self.BackendObject.Encoding
	
	def _setEncoding(self, val):
		self.BackendObject.Encoding = val
		
	
	def _getIsAdding(self):
		""" Return True if the current record is a new record."""
		if self.RowCount <= 0:
			return False
		recKey = self.pkExpression()
		ret = self._newRecords.has_key(recKey)
		return ret
	

	def _getIsPrefCursor(self):
		return self._isPrefCursor

	def _setIsPrefCursor(self, val):
		self._isPrefCursor = val


	def _getKeyField(self):
		try:
			return self._keyField
		except AttributeError:
			return ""

	def _setKeyField(self, kf):
		if "," in kf:
			flds = [f.strip() for f in kf.split(",")]
			self._keyField = tuple(flds)
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
		
			
	def _getRecord(self):
		try:
			ret = self._cursorRecord
		except AttributeError:
			class CursorRecord(object):
				def __init__(self):
					self.cursor = None
					super(CursorRecord, self).__init__()
				
				def __getattr__(self, att):
					return self.cursor.getFieldVal(att)
			
				def __setattr__(self, att, val):
					if att in ("cursor", ):
						super(CursorRecord, self).__setattr__(att, val)
					else:
						self.cursor.setFieldVal(att, val)
			
			ret = self._cursorRecord = CursorRecord()
			self._cursorRecord.cursor = self
		return ret


	def _getRowCount(self):
		try:
			ret = len(self._records)
		except AttributeError:
			ret = -1
		return ret
		

	def _getRowNumber(self):
		try:
			ret = self.__rownumber
		except AttributeError:
			ret = -1
		return ret

	
	def _setRowNumber(self, num):
		self.__rownumber = num
	

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


	def _getVirtualFields(self):
		return getattr(self, "_virtualFields", {})

	def _setVirtualFields(self, val):
		assert isinstance(val, dict)
		self._virtualFields = val


	AutoCommit = property(_getAutoCommit, _setAutoCommit, None,
			_("Do we need explicit begin/commit/rollback commands for transactions?  (bool)"))
	
	AutoPopulatePK = property(_getAutoPopulatePK, _setAutoPopulatePK, None,
			_("When inserting a new record, does the backend populate the PK field?")) 
	
	AutoQuoteNames = property(_getAutoQuoteNames, _setAutoQuoteNames, None,
			_("""When True (default), table and column names are enclosed with 
			quotes during SQL creation.  (bool)"""))
	
	AutoSQL = property(_getAutoSQL, None, None,
			_("Returns the SQL statement automatically generated by the sql manager."))

	AuxCursor = property(_getAuxCursor, None, None,
			_("""Auxiliary cursor object that handles queries that would otherwise
			affect the main cursor's data set.  (dCursorMixin subclass)""")) 
	
	BackendObject = property(_getBackendObject, _setBackendObject, None,
			_("Returns a reference to the object defining backend-specific behavior (dBackend)")) 
	
	CurrentSQL = property(_getCurrentSQL, None, None,
			_("Returns the current SQL that will be run, which is one of UserSQL or AutoSQL."))

	DataStructure = property(_getDataStructure, _setDataStructure, None,
			_("""Returns the structure of the cursor in a tuple of 6-tuples.

				0: field alias (str)
				1: data type code (str)
				2: pk field (bool)
				3: table name (str)
				4: field name (str)
				5: field scale (int or None)

				This information will try to come from a few places, in order:
				1) The explicitly-set DataStructure property
				2) The backend table method"""))

	Encoding = property(_getEncoding, _setEncoding, None,
			_("Encoding type used by the Backend  (string)") )
			
	FieldDescription = property(_getDescrip, None, None,
			_("Tuple of field names and types, as returned by the backend  (tuple)") )
			
	IsAdding = property(_getIsAdding, None, None,
			_("Returns True if the current record is new and unsaved"))
			
	IsPrefCursor = property(_getIsPrefCursor, _setIsPrefCursor, None,
			_("""Returns True if this cursor is used for managing internal 
			Dabo preferences and settings. Default=False.  (bool)"""))
	
	LastSQL = property(_getLastSQL, None, None,
			_("Returns the last executed SQL statement."))

	KeyField = property(_getKeyField, _setKeyField, None,
			_("Name of field that is the PK. If multiple fields make up the key, "
			"separate the fields with commas. (str)"))
	
	Record = property(_getRecord, None, None,
			_("""Represents a record in the data set. You can address individual
			columns by referring to 'self.Record.fieldName' (read-only) (no type)"""))
	
	RowNumber = property(_getRowNumber, _setRowNumber, None,
			_("Current row in the recordset."))
	
	RowCount = property(_getRowCount, None, None,
			_("Current number of rows in the recordset. Read-only."))

	Table = property(_getTable, _setTable, None,
			_("The name of the table in the database that this cursor is updating."))
			
	UserSQL = property(_getUserSQL, _setUserSQL, None,
			_("SQL statement to run. If set, the automatic SQL builder will not be used."))

	VirtualFields = property(_getVirtualFields, _setVirtualFields, None,
			_("""A dictionary mapping virtual_field_name to a function to call.

			The specified function will be called when getFieldVal() is called on 
			the specified field name."""))

