# -*- coding: utf-8 -*-
import types
import re
import dabo
import dabo.dConstants as kons
from dabo.db.dCursorMixin import dCursorMixin
from dabo.dLocalize import _
import dabo.dException as dException
from dabo.dObject import dObject


class dBizobj(dObject):
	""" The middle tier, where the business logic resides."""
	# Class to instantiate for the cursor object
	dCursorMixinClass = dCursorMixin
	# Tell dObject that we'll call before and afterInit manually:
	_call_beforeInit, _call_afterInit, _call_initProperties = False, False, False


	def __init__(self, conn, properties=None, *args, **kwargs):
		""" User code should override beforeInit() and/or afterInit() instead."""
		self.__att_try_setFieldVal = False
		# Collection of cursor objects. MUST be defined first.
		self.__cursors = {}
		# PK of the currently-selected cursor
		self.__currentCursorKey = None
		self._dataStructure = None

		# Dictionary holding any default values to apply when a new record is created. This is
		# now the DefaultValues property (used to be self.defaultValues attribute)
		self._defaultValues = {}

		self._beforeInit()
		cf = self._cursorFactory = conn
		if cf:
			# Base cursor class : the cursor class from the db api
			self.dbapiCursorClass = cf.getDictCursorClass()

			# If there are any problems in the createCursor process, an
			# exception will be raised in that method.
			self.createCursor()

		# We need to make sure the cursor is created *before* the call to
		# initProperties()
		self._initProperties()
		super(dBizobj, self).__init__(properties=properties, *args, **kwargs)
		self._afterInit()
		self.__att_try_setFieldVal = True


	def _beforeInit(self):
		# Cursor to manage SQL Builder info.
		self._sqlMgrCursor = None
		self._cursorFactory = None
		self.__params = ()		# tuple of params to be merged with the sql in the cursor
		self.__children = []		# Collection of child bizobjs
		self._baseClass = dBizobj
		self.__areThereAnyChanges = False	# Used by the isChanged() method.
		# Next two are used by the scan() method.
		self.__scanRestorePosition = True
		self.__scanReverse = False
		# Used by the LinkField property
		self._linkField = ""
		self._parentLinkField = ""
		# Used the the _addChildByRelationDict() method to eliminate infinite loops
		self.__relationDictSet = False
		# Do we try to same on the same record during a requery?
		self._restorePositionOnRequery = True

		# Various attributes used for Properties
		self._caption = ""
		self._dataSource = ""
		self._SQL = ""
		self._requeryOnLoad = False
		self._parent  = None
		self._autoPopulatePK = True
		self._autoQuoteNames = True
		self._keyField = ""
		self._requeryChildOnSave = False
		self._newRecordOnNewParent = False
		self._newChildOnNew = False
		self._fillLinkFromParent = False
		self.exitScan = False

		##########################################
		### referential integrity stuff ####
		##########################################
		### Possible values for each type (not all are relevant for each action):
		### IGNORE - don't worry about the presence of child records
		### RESTRICT - don't allow action if there are child records
		### CASCADE - changes to the parent are cascaded to the children
		self.deleteChildLogic = kons.REFINTEG_CASCADE  # child records will be deleted
		self.updateChildLogic = kons.REFINTEG_IGNORE   # parent keys can be changed w/o
		                                            # affecting children
		self.insertChildLogic = kons.REFINTEG_IGNORE   # child records can be inserted
		                                            # even if no parent record exists.
		##########################################

		self.beforeInit()


	def getTempCursor(self):
		"""Occasionally it is useful to be able to run ad-hoc queries against
		the database. For these queries, where the results are not meant to
		be managed as in regular bizobj/cursor relationships, a temp cursor
		will allow you to run those queries, get the results, and then dispose
		of the cursor.
		"""
		cf = self._cursorFactory
		cursorClass = self._getCursorClass(self.dCursorMixinClass,
				self.dbapiCursorClass)
		crs = cf.getCursor(cursorClass)
		crs.BackendObject = cf.getBackendObject()
		crs.setCursorFactory(cf.getCursor, cursorClass)
		return crs
		

	def createCursor(self, key=None):
		""" Create the cursor that this bizobj will be using for data, and store it
		in the dictionary for cursors, with the passed value of 'key' as its dict key.
		For independent bizobjs, that key will be None.

		Subclasses should override beforeCreateCursor() and/or afterCreateCursor()
		instead of overriding this method, if possible. Returning any non-empty value
		from beforeCreateCursor() will prevent the rest of this method from
		executing.
		"""
		if self.__cursors:
			_dataStructure = getattr(self.__cursors[self.__cursors.keys()[0]], "_dataStructure", None)
			_virtualFields = getattr(self.__cursors[self.__cursors.keys()[0]], "_virtualFields", {})
		else:
			# The first cursor is being created, before DataStructure is assigned.
			_dataStructure = None
			_virtualFields = {}
		errMsg = self.beforeCreateCursor()
		if errMsg:
			raise dException.dException, errMsg

		cursorClass = self._getCursorClass(self.dCursorMixinClass,
				self.dbapiCursorClass)

		if key is None:
			key = self.__currentCursorKey

		cf = self._cursorFactory
		self.__cursors[key] = cf.getCursor(cursorClass)
		self.__cursors[key].setCursorFactory(cf.getCursor, cursorClass)

		crs = self.__cursors[key]
		if _dataStructure is not None:
			crs._dataStructure = _dataStructure
		crs._virtualFields = _virtualFields
		crs.KeyField = self.KeyField
		crs.Table = self.DataSource
		crs.AutoPopulatePK = self.AutoPopulatePK
		crs.AutoQuoteNames = self.AutoQuoteNames
		crs.BackendObject = cf.getBackendObject()
		crs.sqlManager = self.SqlManager
		crs.AutoCommit = self.AutoCommit
		crs._bizobj = self
		if self.RequeryOnLoad:
			crs.requery()
			self.first()
		self.afterCreateCursor(crs)


	def _getCursorClass(self, main, secondary):
		class cursorMix(main, secondary):
			superMixin = main
			superCursor = secondary
			def __init__(self, *args, **kwargs):
				if hasattr(main, "__init__"):
					apply(main.__init__,(self,) + args, kwargs)
				if hasattr(secondary, "__init__"):
					apply(secondary.__init__,(self,) + args, kwargs)
		return  cursorMix


	def first(self):
		""" Move to the first record of the data set.

		Any child bizobjs will be requeried to reflect the new parent record. If
		there are no records in the data set, an exception will be raised.
		"""
		errMsg = self.beforeFirst()
		if not errMsg:
			errMsg = self.beforePointerMove()
		if errMsg:
			raise dException.BusinessRuleViolation, errMsg

		self._CurrentCursor.first()
		self.requeryAllChildren()

		self.afterPointerMove()
		self.afterFirst()


	def prior(self):
		""" Move to the prior record of the data set.

		Any child bizobjs will be requeried to reflect the new parent record. If
		there are no records in the data set, an exception will be raised.
		"""
		errMsg = self.beforePrior()
		if not errMsg:
			errMsg = self.beforePointerMove()
		if errMsg:
			raise dException.BusinessRuleViolation, errMsg

		self._CurrentCursor.prior()
		self.requeryAllChildren()

		self.afterPointerMove()
		self.afterPrior()


	def next(self):
		""" Move to the next record of the data set.

		Any child bizobjs will be requeried to reflect the new parent record. If
		there are no records in the data set, an exception will be raised.
		"""
		errMsg = self.beforeNext()
		if not errMsg:
			errMsg = self.beforePointerMove()
		if errMsg:
			raise dException.BusinessRuleViolation, errMsg

		self._CurrentCursor.next()
		self.requeryAllChildren()

		self.afterPointerMove()
		self.afterNext()


	def last(self):
		""" Move to the last record of the data set.

		Any child bizobjs will be requeried to reflect the new parent record. If
		there are no records in the data set, an exception will be raised.
		"""
		errMsg = self.beforeLast()
		if not errMsg:
			errMsg = self.beforePointerMove()
		if errMsg:
			raise dException.BusinessRuleViolation, errMsg

		self._CurrentCursor.last()
		self.requeryAllChildren()

		self.afterPointerMove()
		self.afterLast()


	def saveAll(self, startTransaction=False, topLevel=True):
		"""Saves all changes to the bizobj and children."""
		useTransact = startTransaction or topLevel
		cursor = self._CurrentCursor
		current_row = self.RowNumber

		if useTransact:
			# Tell the cursor to begin a transaction, if needed.
			cursor.beginTransaction()
		
		changed_rows = self.getChangedRows()
		for row in changed_rows:
			self._moveToRowNum(row)
			try:
				self.save(startTransaction=False, topLevel=False)
			except dException.ConnectionLostException, e:
				self.RowNumber = current_row
				raise dException.ConnectionLostException, e
			except dException.DBQueryException, e:
				# Something failed; reset things.
				if useTransact:
					cursor.rollbackTransaction()
				# Pass the exception to the UI
				self.RowNumber = current_row
				raise dException.DBQueryException, e
			except dException.dException, e:
				if useTransact:
					cursor.rollbackTransaction()
				self.RowNumber = current_row
				raise

		if useTransact:
			cursor.commitTransaction()

		if current_row >= 0:
			try:
				self.RowNumber = current_row
			except: pass


	def save(self, startTransaction=False, topLevel=True):
		"""Save any changes that have been made in the current row.

		If the save is successful, the saveAll() of all child bizobjs will be
		called as well.
		"""
		cursor = self._CurrentCursor
		errMsg = self.beforeSave()
		if errMsg:
			raise dException.BusinessRuleViolation, errMsg

		if self.KeyField is None:
			raise dException.MissingPKException, _("No key field defined for table: ") + self.DataSource

		# Validate any changes to the data. If there is data that fails
		# validation, an Exception will be raised.
		self._validate()

		useTransact = startTransaction or topLevel
		if useTransact:
			# Tell the cursor to begin a transaction, if needed.
			cursor.beginTransaction()

		# Save to the Database, but first save the IsAdding flag as the save() call
		# will reset it to False:
		isAdding = self.IsAdding
		try:
			cursor.save()
			if isAdding:
				# Call the hook method for saving new records.
				self._onSaveNew()

			# Iterate through the child bizobjs, telling them to save themselves.
			for child in self.__children:
				# No need to start another transaction. And since this is a child bizobj,
				# we need to save all rows that have changed.
				if child.RowCount > 0:
					child.saveAll(startTransaction=False, topLevel=False)

			# Finish the transaction, and requery the children if needed.
			if useTransact:
				cursor.commitTransaction()
			if self.RequeryChildOnSave:
				self.requeryAllChildren()

		except dException.ConnectionLostException, e:
			raise 

		except dException.NoRecordsException, e:
			raise

		except dException.DBQueryException, e:
			# Something failed; reset things.
			if useTransact:
				cursor.rollbackTransaction()
			# Pass the exception to the UI
			raise dException.DBQueryException, e

		except dException.dException, e:
			# Something failed; reset things.
			if useTransact:
				cursor.rollbackTransaction()
			# Pass the exception to the UI
			raise

		# Some backends (Firebird particularly) need to be told to write
		# their changes even if no explicit transaction was started.
		cursor.flush()

		# Two hook methods: one specific to Save(), and one which is called after any change
		# to the data (either save() or delete()).
		self.afterChange()
		self.afterSave()


	def cancelAll(self, ignoreNoRecords=None):
		"""Cancel all changes made to the current dataset, including all children."""
		self.scanChangedRows(self.cancel, allCursors=False, ignoreNoRecords=ignoreNoRecords)


	def cancel(self, ignoreNoRecords=None):
		"""Cancel all changes to the current record and all children.

		Two hook methods will be called: beforeCancel() and afterCancel(). The
		former, if it returns an error message, will raise an exception and not
		continue cancelling the record.
		"""
		errMsg = self.beforeCancel()
		if errMsg:
			raise dException.BusinessRuleViolation, errMsg
		if ignoreNoRecords is None:
			# Canceling changes when there are no records should 
			# normally not be a problem.
			ignoreNoRecords = True

		# Tell the cursor and all children to cancel themselves:
		self._CurrentCursor.cancel(ignoreNoRecords=ignoreNoRecords)
		for child in self.__children:
			child.cancelAll(ignoreNoRecords=ignoreNoRecords)

		self.afterCancel()
		
	
	def deleteAllChildren(self, startTransaction=False):
		"""Delete all children associated with the current record without
		deleting the current record in this bizobj.
		"""
		cursor = self._CurrentCursor
		errMsg = self.beforeDeleteAllChildren()
		if errMsg:
			raise dException.BusinessRuleViolation, errMsg

		if startTransaction:
			cursor.beginTransaction()

		try:
			for child in self.__children:
				child.deleteAll(startTransaction=False)
			if startTransaction:
				cursor.commitTransaction()
			self.afterDeleteAllChildren()

		except dException.DBQueryException, e:
			if startTransaction:
				cursor.rollbackTransaction()
			raise dException.DBQueryException, e
		except StandardError, e:
			if startTransaction:
				cursor.rollbackTransaction()
			raise StandardError, e


	def delete(self, startTransaction=False):
		"""Delete the current row of the data set."""
		cursor = self._CurrentCursor
		errMsg = self.beforeDelete()
		if not errMsg:
			errMsg = self.beforePointerMove()
		if errMsg:
			raise dException.BusinessRuleViolation, errMsg

		if self.KeyField is None:
			raise dException.dException, _("No key field defined for table: ") + self.DataSource

		if self.deleteChildLogic == kons.REFINTEG_RESTRICT:
			# See if there are any child records
			for child in self.__children:
				if child.RowCount > 0:
					raise dException.dException, _("Deletion prohibited - there are related child records.")

		if startTransaction:
			cursor.beginTransaction()

		try:
			cursor.delete()
			if self.RowCount == 0:
				# Hook method for handling the deletion of the last record in the cursor.
				self.onDeleteLastRecord()
			# Now cycle through any child bizobjs and fire their cancel() methods. This will
			# ensure that any changed data they may have is reverted. They are then requeried to
			# populate them with data for the current record in this bizobj.
			for child in self.__children:
				if self.deleteChildLogic == kons.REFINTEG_CASCADE:
					child.deleteAll(startTransaction=False)
				else:
					child.cancelAll()
					child.requery()
					
			if startTransaction:
				cursor.commitTransaction()
				
			# Some backends (Firebird particularly) need to be told to write 
			# their changes even if no explicit transaction was started.
			cursor.flush()
			
			self.afterPointerMove()
			self.afterChange()
			self.afterDelete()
		except dException.DBQueryException, e:
			if startTransaction:
				cursor.rollbackTransaction()
			raise dException.DBQueryException, e
		except StandardError, e:
			if startTransaction:
				cursor.rollbackTransaction()
			raise StandardError, e


	def deleteAll(self, startTransaction=False):
		""" Delete all rows in the data set."""
		while self.RowCount > 0:
			self.first()
			ret = self.delete(startTransaction)


	def execute(self, sql):
		"""Execute the sql on the cursor. Dangerous. Use executeSafe instead."""
		return self._CurrentCursor.execute(sql)


	def executeSafe(self, sql):
		"""Execute the passed SQL using an auxiliary cursor.

		This is considered 'safe', because it won't harm the contents of the
		main cursor.
		"""
		return self._CurrentCursor.executeSafe(sql)


	def getChangedRows(self):
		""" Returns a list of row numbers for which isChanged()	returns True. The 
		changes may therefore not be in the record itself, but in a dependent child 
		record.
		"""
		if self.__children:
			# Must iterate all records to find potential changes in children:
			self.__changedRows = []
			self.scan(self._listChangedRows)
			return self.__changedRows
		else:
			# Can use the much faster cursor.getChangedRows():
			return self._CurrentCursor.getChangedRows()


	def _listChangedRows(self):
		""" Called from a scan loop. If the current record is changed,
		append the RowNumber to the list.
		"""
		if self.isChanged():
			self.__changedRows.append(self.RowNumber)


	def getRecordStatus(self, rownum=None):
		""" Returns a dictionary containing an element for each changed
		field in the specified record (or the current record if none is specified).
		The field name is the key for each element; the value is a 2-element
		tuple, with the first element being the original value, and the second
		being the current value.
		"""
		if rownum is None:
			rownum = self.RowNumber
		return self._CurrentCursor.getRecordStatus(rownum)


	def scan(self, func, *args, **kwargs):
		"""Iterate over all records and apply the passed function to each.

		Set self.exitScan to True to exit the scan on the next iteration.

		If self.__scanRestorePosition is True, the position of the current
		record in the recordset is restored after the iteration. If
		self.__scanReverse is true, the records are processed in reverse order.
		"""
		self.scanRows(func, range(self.RowCount), *args, **kwargs)


	def scanRows(self, func, rows, *args, **kwargs):
		"""Iterate over the specified rows and apply the passed function to each.

		Set self.exitScan to True to exit the scan on the next iteration.
		"""
		# Flag that the function can set to prematurely exit the scan
		self.exitScan = False
		rows = list(rows)
		if self.__scanRestorePosition:
			try:
				currPK = self.getPK()
				currRow = None
			except:
				# No PK defined
				currPK = None
				currRow = self.RowNumber
		try:
			if self.__scanReverse:
				rows.reverse()
			for i in rows:
				self._moveToRowNum(i)
				func(*args, **kwargs)
				if self.exitScan:
					break
		except dException.dException, e:
			if self.__scanRestorePosition:
				self.RowNumber = currRow
			raise dException.dException, e

		if self.__scanRestorePosition:
			if currPK is not None:
				self._positionUsingPK(currPK, updateChildren=False)
			else:
				try:
					self.RowNumber = currRow
				except StandardError, e:
					# Perhaps the row was deleted; at any rate, leave the pointer
					# at the end of the data set
					row = self.RowCount  - 1
					if row >= 0:
						self.RowNumber = row
		

	def scanChangedRows(self, func, allCursors=False, *args, **kwargs):
		"""Move the record pointer to each changed row, and call func.

		If allCursors is True, all other cursors for different parent records will 
		be iterated as well. 

		If you want to end the scan on the next iteration, set self.exitScan=True.

		Records are scanned in arbitrary order. Any exception raised by calling
		func() will be passed	up to the caller.
		"""
		self.exitScan = False
		old_currentCursorKey = self.__currentCursorKey
		try:
			old_pk = self._CurrentCursor.getPK()
		except dException.NoRecordsException:
			# no rows to scan
			return

		if allCursors:
			cursors = self.__cursors
		else:
			cursors = {old_pk: self._CurrentCursor}

		for key, cursor in cursors.iteritems():
			self._CurrentCursor = key
			changed_keys = list(set(cursor._mementos.keys() + cursor._newRecords.keys()))
			for pk in changed_keys:
				self._positionUsingPK(pk)
				try:
					func(*args, **kwargs)
				except:
					# Reset things and bail:
					self._CurrentCursor = old_currentCursorKey
					self._positionUsingPK(old_pk)
					raise
		
		self._CurrentCursor = old_currentCursorKey
		if old_pk is not None:
			self._positionUsingPK(old_pk)


	def getFieldNames(self):
		"""Returns a tuple of all the field names in the cursor."""
		flds = self._CurrentCursor.getFields()
		# This is a tuple of 3-tuples; we just want the names
		return tuple([ff[0] for ff in flds])


	def replace(self, field, valOrExpr, scope=None):
		"""Replaces the value of the specified field with the given value
		or expression. All records matching the scope are affected; if
		no scope is specified, all records are affected.

		'valOrExpr' will be treated as a literal value, unless it is prefixed
		with an equals sign. All expressions will therefore be a string
		beginning with '='. Literals can be of any type.
		"""
		self._CurrentCursor.replace(field, valOrExpr, scope=scope)


	def new(self):
		""" Create a new record and populate it with default values. Default
		values are specified in the DefaultValues dictionary.
		"""
		errMsg = self.beforeNew()
		if not errMsg:
			errMsg = self.beforePointerMove()
		if errMsg:
			raise dException.BusinessRuleViolation, errMsg

		self._CurrentCursor.new()
		self._onNew()

		# Update all child bizobjs
		self.requeryAllChildren()

		if self.NewChildOnNew:
			# Add records to all children set to have records created on a new parent record.
			for child in self.__children:
				if child.NewRecordOnNewParent:
					child.new()

		self.afterPointerMove()
		self.afterNew()


	def setSQL(self, sql=None):
		""" Set the SQL query that will be executed upon requery().

		This allows you to manually override the sql executed by the cursor. If no
		sql is passed, the SQL will get set to the value returned by getSQL().
		"""
		if sql is None:
			# sql not passed; get it from the sql mixin:
			# Set the appropriate child filter on the link field
			self.setChildLinkFilter()

			self.SQL = self.getSQL()
		else:
			# sql passed; set it explicitly
			self.SQL = sql


	def requery(self):
		""" Requery the data set.

		Refreshes the data set with the current values in the database,
		given the current state of the filtering parameters.
		"""
		errMsg = self.beforeRequery()
		if errMsg:
			raise dException.BusinessRuleViolation, errMsg
		if self.KeyField is None:
			errMsg = _("No Primary Key defined in the Bizobj for %s") % self.DataSource
			raise dException.MissingPKException, errMsg

		# If this is a dependent (child) bizobj, this will enforce the relation
		self.setChildLinkFilter()

		# Hook method for creating the param list
		params = self.getParams()

		# Record this in case we need to restore the record position
		try:
			currPK = self.getPK()
		except dException.NoRecordsException:
			currPK = None

		# run the requery
		cursor = self._CurrentCursor
		try:
			cursor.requery(params)

		except dException.ConnectionLostException, e:
			raise dException.ConnectionLostException, e

		except dException.DBQueryException, e:
			# Something failed; reset things.
			cursor.rollbackTransaction()
			# Pass the exception to the UI
			raise dException.DBQueryException, e

		except dException.dException, e:
			# Something failed; reset things.
			cursor.rollbackTransaction()
			# Pass the exception to the UI
			raise dException.dException, e

		if self.RestorePositionOnRequery:
			self._positionUsingPK(currPK)

		try:
			self.requeryAllChildren()
		except dException.NoRecordsException:
			pass
		self.afterRequery()


	def setChildLinkFilter(self):
		""" If this is a child bizobj, its record set is dependent on its parent's
		current PK value. This will add the appropriate WHERE clause to
		filter the child records. If the parent is a new, unsaved record,
		there cannot be any child records saved yet, so an empty query
		is built.
		"""
		if self.DataSource and self.LinkField and self.Parent:
			if self.Parent.IsAdding:
				# Parent is new and not yet saved, so we cannot have child records yet.
				self.setWhereClause("")
				filtExpr = " 1 = 0 "
			else:
				if self.ParentLinkField:
					# The link to the parent is something other than the PK
					val = self.escQuote(self.Parent.getFieldVal(self.ParentLinkField))
				else:
					val = self.escQuote(self.getParentPK())
				linkFieldParts = self.LinkField.split(".")
				if len(linkFieldParts) < 2:
					dataSource = self.DataSource
					linkField = self.LinkField
				else:
					# The source table was specified in the LinkField
					dataSource = linkFieldParts[0]
					linkField = linkFieldParts[1]
				filtExpr = " %s.%s = %s " % (dataSource, linkField, val)
			self._CurrentCursor.setChildFilterClause(filtExpr)


	def sort(self, col, ord=None, caseSensitive=True):
		""" Sort the rows based on values in a specified column.

		Called when the data is to be sorted on a particular column
		in a particular order. All the checking on the parameters is done
		in the cursor.
		"""
		try:
			cc = self._CurrentCursor
		except:
			cc = None
		if cc is not None:
			self._CurrentCursor.sort(col, ord, caseSensitive)


	def setParams(self, params):
		""" Set the query parameters for the cursor.

		Accepts a tuple that will be merged with the sql statement using the
		cursor's standard method for merging.
		"""
		if not isinstance(params, tuple):
			params = (params, )
		self.__params = params


	def _validate(self):
		""" Internal method. User code should override validateRecord().

		_validate() is called by the save() routine before saving any data.
		If any data fails validation, an exception will be raised, and the
		save() will not be allowed to proceed.
		"""
		errMsg = ""
		if self.isChanged():
			# No need to validate if the data hasn't changed
			message = self.validateRecord()
			if message:
				errMsg += message
		if errMsg:
			raise dException.BusinessRuleViolation, errMsg


	def validateRecord(self):
		""" Hook for subclass business rule validation code.

		This is the method that you should customize in your subclasses
		to create checks on the data entered by the user to be sure that it
		conforms to your business rules. Your validation code should return
		an error message that describes the reason why the data is not
		valid; this message will be propagated back up to the UI where it can
		be displayed to the user so that they can correct the problem.
		Example:

			if not myNonEmptyField:
				return "MyField must not be blank"

		It is assumed that we are on the correct record for testing before
		this method is called.
		"""
		pass


	def fieldValidation(self, fld, val):
		"""This is called by the form when a control that is marked for field-
		level validation loses focus. It handles communication between the
		bizobj methods and the form. When creating Dabo apps, if you want
		to add field-level validation rules, you should override fieldValidation()
		with your specific code.
		"""
		errMsg = ""
		message = self.validateField(fld, val)
		if message == kons.BIZ_DEFAULT_FIELD_VALID:
			# No validation was done
			return
		if message:
			errMsg += message
		if errMsg:
			raise dException.BusinessRuleViolation, errMsg
		else:
			raise dException.BusinessRulePassed


	def validateField(self, fld, val):
		"""This is the method to override if you need field-level validation
		to your app. It will receive the field name and the new value; you can
		then apply your business rules to determine if the new value is
		valid. If not, return a string describing the problem. Any non-empty
		return value from this method will prevent the control's value
		from being changed.
		"""
		return kons.BIZ_DEFAULT_FIELD_VALID


	def _moveToRowNum(self, rownum, updateChildren=True):
		""" For internal use only! Should never be called from a developer's code.
		It exists so that a bizobj can move through the records in its cursor
		*without* firing additional code.
		"""
		self._CurrentCursor.moveToRowNum(rownum)
		if updateChildren:
			pk = self.getPK()
			for child in self.__children:
				# Let the child know the current dependent PK
				child.setCurrentParent(pk)


	def _positionUsingPK(self, pk, updateChildren=True):
		""" For internal use only! Should never be called from a developer's code.
		It exists so that a bizobj can move through the records in its cursor
		*without* firing additional code.
		"""
		self._CurrentCursor.moveToPK(pk)
		if updateChildren:
			for child in self.__children:
				# Let the child know the current dependent PK
				child.setCurrentParent(pk)


	def moveToPK(self, pk):
		"""Move to the row with the specified pk value, or raise RowNotFoundException."""
		row = self.seek(pk, self.KeyField, caseSensitive=True, near=False,
				runRequery=True)
		if row == -1:
			raise dabo.dException.RowNotFoundException, _("PK Value %s not found in the dataset") % pk


	def seek(self, val, fld=None, caseSensitive=False,
			near=False, runRequery=False):
		""" Search for a value in a field, and move the record pointer to the match.

		Used for searching of the bizobj's cursor for a particular value in a
		particular field. Can be optionally case-sensitive.

		If 'near' is True, and no exact match is found in the cursor, the cursor's
		record pointer will be placed at the record whose value in that field
		is closest to the desired value without being greater than the requested
		value.

		If runRequery is True, and the record pointer is moved, all child bizobjs
		will be requeried, and the afterPointerMove() hook method will fire.

		Returns the RowNumber of the found record, or -1 if no match found.
		"""
		ret = self._CurrentCursor.seek(val, fld, caseSensitive, near)
		if ret != -1:
			if runRequery:
				self.requeryAllChildren()
				self.afterPointerMove()
		return ret


	def isAnyChanged(self, parentPK=None):
		"""Returns True if any record in the current record set has been changed."""
		if parentPK is None:
			try:
				cc = self._CurrentCursor
			except:
				cc = None
		else:
			cc = self.__cursors.get(parentPK, None)
		if cc is None:
			# No cursor, no changes.
			return False
		
		if cc.isChanged(allRows=True):
			return True
	
		# Nothing's changed in the top level, so we need to recurse the children:
		try:
			pk = self.getPK()
		except dException.NoRecordsException:
			# If there are no records, there can be no changes
			return False
			
		for child in self.__children:
			if child.isAnyChanged(parentPK=pk):
				return True
		# If we made it to here, there are no changes.
		return False


	def isChanged(self):
		""" Return True if data has changed in this bizobj and any children.

		By default, only the current record is checked. Call isAnyChanged() to
		check all records.
		"""
		try:
			cc = self._CurrentCursor
		except:
			cc = None
		if cc is None:
			# No cursor, no changes.
			return False
		ret = cc.isChanged(allRows=False)

		if not ret:
			# see if any child bizobjs have changed
			try:
				pk = self.getPK()
			except dException.NoRecordsException:
				# If there are no records, there can be no changes
				return False
			for child in self.__children:
				ret = child.isAnyChanged(parentPK=pk)
				if ret:
					break
		return ret


	def onDeleteLastRecord(self):
		""" Hook called when the last record has been deleted from the data set."""
		pass


	def _onSaveNew(self):
		""" Called after successfully saving a new record."""
		# If this is a new parent record with a new auto-generated PK, pass it on
		# to the children before they save themselves.
		if self.AutoPopulatePK:
			pk = self.getPK()
			for child in self.__children:
				child.setParentFK(pk)
		# Call the custom hook method
		self.onSaveNew()


	def onSaveNew(self):
		""" Hook method called after successfully saving a new record."""
		pass


	def _onNew(self):
		""" Populate the record with any default values.

		User subclasses should leave this alone and instead override onNew().
		"""
		cursor = self._CurrentCursor
		currKey = self.__currentCursorKey
		if self.AutoPopulatePK:
			# Provide a temporary PK so that any linked children can be properly
			# identified until the record is saved and a permanent PK is obtained.
			tmpKey = cursor.genTempAutoPK()
			if currKey is None:
				self.__currentCursorKey = tmpKey
				del self.__cursors[currKey]
				self.__cursors[tmpKey] = cursor
		# Fill in the link to the parent record
		if self.Parent and self.FillLinkFromParent and self.LinkField:
			self.setParentFK()
		cursor.setDefaults(self.DefaultValues)
		cursor.setNewFlag()

		# Call the custom hook method
		self.onNew()

		# Remove the memento for the new record, as we want to only record
		# changes made after this point.
		cursor._clearMemento()


	def onNew(self):
		"""Called when a new record is added. 

		Use this hook to add additional default field values, or anything else 
		you need. If you change field values here, the memento system will not
		catch it (the record will not be marked 'dirty'). Use afterNew() if you
		instead want the memento system to record the changes.
		"""
	pass


	def setParentFK(self, val=None):
		""" Accepts and sets the foreign key value linking to the
		parent table for all records.
		"""
		if self.LinkField:
			if val is None:
				val = self.getParentPK()
			self.scan(self._setParentFK, val)

	def _setParentFK(self, val):
		self.setFieldVal(self.LinkField, val)


	def setCurrentParent(self, val=None, fromChildRequery=None):
		""" Lets dependent child bizobjs know the current value of their parent
		record.
		"""
		if self.LinkField:
			if val is None and not fromChildRequery:
				val = self.getParentPK()
			# Update the key value for the cursor
			self.__currentCursorKey = val
			# Make sure there is a cursor object for this key.
			self._CurrentCursor = val


	def addChild(self, child):
		""" Add the passed child bizobj to this bizobj.

		During the creation of the form, child bizobjs are added by the parent.
		This stores the child reference here, and sets the reference to the
		parent in the child.
		"""
		if child not in self.__children:
			self.__children.append(child)
			child.Parent = self


	def _addChildByRelationDict(self, dict, bizModule):
		""" Deprecated; used in old datanav framework."""
		addedChildren = []
		if self.__relationDictSet:
			# already done this...
			return addedChildren
		self.__relationDictSet = True

		myRelations = [ dict[k] for k in dict.keys()
				if dict[k]["source"].lower() == self.DataSource.lower() ]
		if not myRelations:
			return addedChildren

		for relation in myRelations:
			if relation["relationType"] == "1M":
				# Each 'relation' is a dict with the following structure:
				# 'target': child table
				# 'targetField': field in child table linked to parent
				# 'source': parent table
				# 'sourceField': field in parent table linked to child
				target = relation["target"]
				targetField = relation["targetField"]
				source = relation["source"]
				sourceField = relation["sourceField"]

				if self.getAncestorByDataSource(target):
					# The 'child' already exists as an ancestor of this bizobj. This can
					# happen in many-to-many relationships. We don't want to add it,
					# as this creates infinite loops.
					continue

				childBiz = self.getChildByDataSource(target)
				if not childBiz:
					# target is the datasource of the bizobj to find.
					childBizClass = None
					for candidate, candidateClass in bizModule.__dict__.items():
						if type(candidateClass) == type:
							candidateInstance = candidateClass(self._cursorFactory)
							if candidateInstance.DataSource.lower() == target.lower():
								childBizClass = candidateClass

					childBiz = childBizClass(self._cursorFactory)
					self.addChild(childBiz)
					addedChildren.append(childBiz)
					childBiz.LinkField = targetField
					childBiz.FillLinkFromParent = True
					if sourceField != self.KeyField:
						childBiz.ParentLinkField = sourceField
				# Now pass this on to the child
				addedGrandChildren = childBiz.addChildByRelationDict(dict, bizModule)
				for gc in addedGrandChildren:
					addedChildren.append(gc)
		return addedChildren


	def getAncestorByDataSource(self, ds):
		ret = None
		if self.Parent:
			if self.Parent.DataSource == ds:
				ret = self.Parent
			else:
				ret = self.Parent.getAncestorByDataSource(ds)
		return ret


	def requeryAllChildren(self):
		""" Requery each child bizobj's data set.

		Called to assure that all child bizobjs have had their data sets
		refreshed to match the current master row. This will normally happen
		automatically when appropriate, but user code may call this as well
		if needed.
		"""
		if len(self.__children) == 0:
			return True

		errMsg = self.beforeChildRequery()
		if errMsg:
			raise dException.BusinessRuleViolation, errMsg

		if self.IsAdding and self.AutoPopulatePK:
			pk = None
		else:
			pk = self.getPK()
		for child in self.__children:
			# Let the child know the current dependent PK
			if child.RequeryWithParent:
				child.setCurrentParent(pk, fromChildRequery=True)
				if not child.isChanged():
					child.requery()
		self.afterChildRequery()


	def getPK(self):
		""" Return the value of the PK field."""
		if self.KeyField is None:
			raise dException.dException, _("No key field defined for table: ") + self.DataSource
		cc = self._CurrentCursor
		return cc.getFieldVal(cc.KeyField)


	def getParentPK(self):
		""" Return the value of the parent bizobjs' PK field.

		Alternatively, user code can just call self.Parent.getPK().
		"""
		try:
			return self.Parent.getPK()
		except dException.NoRecordsException:
			# The parent bizobj has no records
			return None


	def getFieldVal(self, fld, row=None):
		""" Return the value of the specified field in the current or specified row."""
		cursor = self._CurrentCursor
		if cursor is not None:
			return cursor.getFieldVal(fld, row)


	def setFieldVal(self, fld, val):
		""" Set the value of the specified field in the current row."""
		cursor = self._CurrentCursor
		if cursor is not None:
			try:
				ret = cursor.setFieldVal(fld, val)
			except dException.NoRecordsException:
				ret = False
		return ret	


	def getDataSet(self, flds=(), rowStart=0, rows=None):
		""" Get the entire data set encapsulated in a list.

		If the optional	'flds' parameter is given, the result set will be filtered
		to only include the specified fields. rowStart specifies the starting row
		to include, and rows is the number of rows to return.
		"""
		ret = None
		try:
			cc = self._CurrentCursor
		except:
			cc = None
		if cc is not None:
			ret = self._CurrentCursor.getDataSet(flds, rowStart, rows)
		return ret


	def getDataStructure(self):
		""" Gets the structure of the DataSource table. Returns a list
		of 3-tuples, where the 3-tuple's elements are:
			0: the field name (string)
			1: the field type ('I', 'N', 'C', 'M', 'B', 'D', 'T')
			2: boolean specifying whether this is a pk field.
		"""
		return self._CurrentCursor.getFields(self.DataSource)


	def getDataStructureFromDescription(self):
		""" Gets the structure of the DataSource table. Returns a list
		of 3-tuples, where the 3-tuple's elements are:
			0: the field name (string)
			1: the field type ('I', 'N', 'C', 'M', 'B', 'D', 'T')
			2: boolean specifying whether this is a pk field.
		"""
		return self._CurrentCursor.getFieldInfoFromDescription()


	def getParams(self):
		""" Return the parameters to send to the cursor's execute method.

		This is the place to define the parameters to be used to modify
		the SQL statement used to produce the record set. Normally if you have
		known parameters, you would simply call setParams(<param tuple>).
		But in cases where the parameter values need to be dynamically calculated,
		override this method in your subclass to determine the tuple to return.
		"""
		return self.__params


	def getChildren(self):
		""" Return a tuple of the child bizobjs."""
		ret = []
		for child in self.__children:
			ret.append(child)
		return tuple(ret)


	def getChildByDataSource(self, dataSource):
		""" Return a reference to the child bizobj with the passed dataSource."""
		ret = None
		for child in self.getChildren():
			if child.DataSource == dataSource:
				ret = child
				break
		return ret


	def escQuote(self, val):
		""" Escape special characters in SQL strings.

		Escapes any single quotes that could cause SQL syntax errors. Also
		escapes backslashes, since they have special meaning in SQL parsing.
		Finally, wraps the value in single quotes.
		"""
		return self._CurrentCursor.escQuote(val)


	def formatForQuery(self, val):
		""" Wrap up any value(int, long, string, date, date-time, decimal, none)
		for use to be in a query.
		"""
		return self._CurrentCursor.formatForQuery(val)


	def formatDateTime(self, val):
		""" Wrap a date or date-time value in the format
		required by the backend.
		"""
		return self._CurrentCursor.formatDateTime(val)


	def moveToRowNumber(self, rowNumber):
		""" Move to the specified row number."""
		self.RowNumber = rowNumber


	def getWordMatchFormat(self):
		return self._CurrentCursor.getWordMatchFormat()


	def oldVal(self, fieldName, row=None):
		return self._CurrentCursor.oldVal(fieldName, row)


	########## SQL Builder interface section ##############
	def addField(self, exp, alias=None):
		return self._CurrentCursor.addField(exp, alias)
	def addFrom(self, exp):
		return self._CurrentCursor.addFrom(exp)
	def addJoin(self, tbl, exp, joinType=None):
		return self._CurrentCursor.addJoin(tbl, exp, joinType)
	def addGroupBy(self, exp):
		return self._CurrentCursor.addGroupBy(exp)
	def addOrderBy(self, exp):
		return self._CurrentCursor.addOrderBy(exp)
	def addWhere(self, exp, comp="and"):
		return self._CurrentCursor.addWhere(exp)
	def getSQL(self):
		return self._CurrentCursor.getSQL()
	def setFieldClause(self, clause):
		return self._CurrentCursor.setFieldClause(clause)
	def setFromClause(self, clause):
		return self._CurrentCursor.setFromClause(clause)
	def setJoinClause(self, clause):
		return self._CurrentCursor.setJoinClause(clause)
	def setGroupByClause(self, clause):
		return self._CurrentCursor.setGroupByClause(clause)
	def getLimitClause(self):
		return self._CurrentCursor.getLimitClause()
	def setLimitClause(self, clause):
		return self._CurrentCursor.setLimitClause(clause)
	# For simplicity's sake, create aliases
	setLimit, getLimit = setLimitClause, getLimitClause
	def setOrderByClause(self, clause):
		return self._CurrentCursor.setOrderByClause(clause)
	def setWhereClause(self, clause):
		return self._CurrentCursor.setWhereClause(clause)
	def prepareWhere(self, clause):
		return self._CurrentCursor.prepareWhere(clause)
	def getFieldClause(self):
		return self._CurrentCursor.getFieldClause()
	def getFromClause(self):
		return self._CurrentCursor.getFromClause()
	def getJoinClause(self):
		return self._CurrentCursor.getJoinClause()
	def getWhereClause(self):
		return self._CurrentCursor.getWhereClause()
	def getGroupByClause(self):
		return self._CurrentCursor.getGroupByClause()
	def getOrderByClause(self):
		return self._CurrentCursor.getOrderByClause()
	########## END - SQL Builder interface section ##############




	########## Pre-hook interface section ##############
	def beforeNew(self): return ""
	def beforeDelete(self): return ""
	def beforeDeleteAllChildren(self): return ""
	def beforeFirst(self): return ""
	def beforePrior(self): return ""
	def beforeNext(self): return ""
	def beforeLast(self): return ""
	def beforeSetRowNumber(self): return ""
	def beforePointerMove(self): return ""
	def beforeSave(self): return ""
	def beforeCancel(self): return ""
	def beforeRequery(self): return ""
	def beforeChildRequery(self): return ""
	def beforeCreateCursor(self): return ""
	########## Post-hook interface section ##############
	def afterNew(self): 
		"""Called after a new record is added. 

		Use this hook to change field values, or anything else you need. If you
		change field values here, the memento system will catch it. If you want
		to change field values and not trigger the memento system, use onNew()
		instead.
		"""
		pass
	def afterDelete(self): pass
	def afterDeleteAllChildren(self): return ""
	def afterFirst(self): pass
	def afterPrior(self): pass
	def afterNext(self): pass
	def afterLast(self): pass
	def afterSetRowNumber(self): pass
	def afterPointerMove(self): pass
	def afterSave(self): pass
	def afterCancel(self): pass
	def afterRequery(self): pass
	def afterChildRequery(self): pass
	def afterChange(self): pass
	def afterCreateCursor(self, cursor): pass


	def _getAutoCommit(self):
		return self._CurrentCursor.AutoCommit

	def _setAutoCommit(self, val):
		self._CurrentCursor.AutoCommit = val


	def _getAutoPopulatePK(self):
		try:
			return self._autoPopulatePK
		except AttributeError:
			return True

	def _setAutoPopulatePK(self, val):
		self._autoPopulatePK = bool(val)
		if self._CurrentCursor:
			self._CurrentCursor.AutoPopulatePK = val


	def _getAutoQuoteNames(self):
		return self._autoQuoteNames

	def _setAutoQuoteNames(self, val):
		self._autoQuoteNames = val
		if self._CurrentCursor:
			self._CurrentCursor.AutoQuoteNames = val


	def _getAutoSQL(self):
		try:
			return self._CurrentCursor.getSQL()
		except:
			return None


	def _getCaption(self):
		try:
			return self._caption
		except AttributeError:
			return self.DataSource

	def _setCaption(self, val):
		self._caption = str(val)


	def _getCurrentSQL(self):
		return self._CurrentCursor.CurrentSQL


	def _getCurrentCursor(self):
		try:
			return self.__cursors[self.__currentCursorKey]
		except (KeyError, AttributeError):
			# There is no current cursor. Try creating one.
			self.createCursor()
			try:
				return self.__cursors[self.__currentCursorKey]
			except KeyError:
				return None

	def _setCurrentCursor(self, val):
		""" Sees if there is a cursor in the cursors dict with a key that matches
		the current parent key. If not, creates one.
		"""
		self.__currentCursorKey = val
		if not self.__cursors.has_key(val):
			self.createCursor()


	def _getDataSource(self):
		try:
			return self._dataSource
		except AttributeError:
			return ""

	def _setDataSource(self, val):
		self._dataSource = str(val)
		cursor = self._CurrentCursor
		if cursor is not None:
			cursor.Table = val


	def _getDataStructure(self):
		# We need to save the explicitly-assigned DataStructure here in the bizobj,
		# so that we are able to propagate it to any future-assigned child cursors.
		_ds = self._dataStructure
		if _ds is not None:
			return _ds
		return self._CurrentCursor.DataStructure

	def _setDataStructure(self, val):
		for key, cursor in self.__cursors.items():
			cursor.DataStructure = val
		self._dataStructure = val

	def _getDefaultValues(self):
		return self._defaultValues

	def _setDefaultValues(self, val):
		self._defaultValues = val


	def _getVirtualFields(self):
		# We need to save the explicitly-assigned VirtualFields here in the bizobj,
		# so that we are able to propagate it to any future-assigned child cursors.
		_df = getattr(self, "_virtualFields", None)
		if _df is not None:
			return _df
		return self._CurrentCursor.VirtualFields

	def _setVirtualFields(self, val):
		for key, cursor in self.__cursors.items():
			cursor.VirtualFields = val
		self._virtualFields = val


	def _getEncoding(self):
		ret = None
		cursor = self._CurrentCursor
		if cursor is not None:
			ret = cursor.Encoding
		if ret is None:
			if self.Application:
				ret = self.Application.Encoding
			else:
				ret = dabo.defaultEncoding
		return ret

	def _setEncoding(self, val):
		cursor = self._CurrentCursor
		if cursor is not None:
			cursor.Encoding = val


	def _getFillLinkFromParent(self):
		try:
			return self._fillLinkFromParent
		except AttributeError:
			return False

	def _setFillLinkFromParent(self, val):
		self._fillLinkFromParent = bool(val)


	def _isAdding(self):
		return self._CurrentCursor.IsAdding


	def _getKeyField(self):
		try:
			return self._keyField
		except AttributeError:
			return ""

	def _setKeyField(self, val):
		self._keyField = val
		cursor = self._CurrentCursor
		if cursor is not None:
			cursor.KeyField = val


	def _getLastSQL(self):
		try:
			v = self._CurrentCursor.LastSQL
		except AttributeError:
			v = None
		return v


	def _getLinkField(self):
		try:
			return self._linkField
		except AttributeError:
			return ""

	def _setLinkField(self, val):
		self._linkField = str(val)


	def _getNewChildOnNew(self):
		try:
			return self._newChildOnNew
		except AttributeError:
			return False

	def _setNewChildOnNew(self, val):
		self._newChildOnNew = bool(val)


	def _getNewRecordOnNewParent(self):
		try:
			return self._newRecordOnNewParent
		except AttributeError:
			return False

	def _setNewRecordOnNewParent(self, val):
		self._newRecordOnNewParent = bool(val)


	def _getNonUpdateFields(self):
		return self._CurrentCursor.getNonUpdateFields()

	def _setNonUpdateFields(self, fldList=None):
		if fldList is None:
			fldList = []
		self._CurrentCursor.setNonUpdateFields(fldList)


	def _getParent(self):
		try:
			return self._parent
		except AttributeError:
			return None

	def _setParent(self, val):
		if isinstance(val, dBizobj):
			self._parent = val
		else:
			raise TypeError, _("Parent must descend from dBizobj")


	def _getParentLinkField(self):
		try:
			return self._parentLinkField
		except AttributeError:
			return ""

	def _setParentLinkField(self, val):
		self._parentLinkField = str(val)


	def _getRecord(self):
		return self._CurrentCursor.Record


	def _getRequeryChildOnSave(self):
		try:
			return self._requeryChildOnSave
		except AttributeError:
			return False

	def _setRequeryChildOnSave(self, val):
		self._requeryChildOnSave = bool(val)


	def _getRequeryOnLoad(self):
		try:
			ret = self._requeryOnLoad
		except AttributeError:
			ret = False
		return ret

	def _setRequeryOnLoad(self, val):
		self._requeryOnLoad = bool(val)


	def _getRestorePositionOnRequery(self):
		try:
			return self._restorePositionOnRequery
		except AttributeError:
			return True

	def _setRestorePositionOnRequery(self, val):
		self._restorePositionOnRequery = bool(val)


	def _getRequeryWithParent(self):
		v = getattr(self, "_requeryWithParent", None)
		if v is None:
			v = self._requeryWithParent = True
		return v

	def _setRequeryWithParent(self, val):
		self._requeryWithParent = bool(val)


	def _getRowCount(self):
		try:
			ret = self._CurrentCursor.RowCount
		except:
			ret = None
		return ret


	def _getRowNumber(self):
		try:
			ret = self._CurrentCursor.RowNumber
		except:
			ret = None
		return ret

	def _setRowNumber(self, rownum):
		errMsg = self.beforeSetRowNumber()
		if not errMsg:
			errMsg = self.beforePointerMove()
		if errMsg:
			raise dException.BusinessRuleViolation, errMsg
		self._moveToRowNum(rownum)
		self.requeryAllChildren()
		self.afterPointerMove()
		self.afterSetRowNumber()


	def _getSQL(self):
		try:
			return self._SQL
		except AttributeError:
			return ""

	def _setSQL(self, val):
		self._SQL = val


	def _getSqlMgr(self):
		if self._sqlMgrCursor is None:
			cursorClass = self._getCursorClass(self.dCursorMixinClass,
					self.dbapiCursorClass)
			cf = self._cursorFactory
			crs = self._sqlMgrCursor = cf.getCursor(cursorClass)
			crs.setCursorFactory(cf.getCursor, cursorClass)
			crs.KeyField = self.KeyField
			crs.Table = self.DataSource
			crs.AutoPopulatePK = self.AutoPopulatePK
			crs.AutoQuoteNames = self.AutoQuoteNames
			crs.BackendObject = cf.getBackendObject()
		return self._sqlMgrCursor


	def _getUserSQL(self):
		try:
			v = self._CurrentCursor.UserSQL
		except AttributeError:
			v = None
		return v

	def _setUserSQL(self, val):
		self._CurrentCursor.UserSQL = val



	### -------------- Property Definitions ------------------  ##
	AutoCommit = property(_getAutoCommit, _setAutoCommit, None,
			_("Do we need explicit begin/commit/rollback commands for transactions?  (bool)"))

	AutoPopulatePK = property(_getAutoPopulatePK, _setAutoPopulatePK, None,
			_("Determines if we are using a table that auto-generates its PKs. (bool)"))

	AutoQuoteNames = property(_getAutoQuoteNames, _setAutoQuoteNames, None,
			_("""When True (default), table and column names are enclosed with 
			quotes during SQL creation in the cursor.  (bool)"""))
	
	AutoSQL = property(_getAutoSQL, None, None,
			_("Returns the SQL statement automatically generated by the sql manager."))

	Caption = property(_getCaption, _setCaption, None,
			_("The friendly title of the cursor, used in messages to the end user. (str)"))

	CurrentSQL = property(_getCurrentSQL, None, None,
			_("Returns the current SQL that will be run, which is one of UserSQL or AutoSQL."))

	_CurrentCursor = property(_getCurrentCursor, _setCurrentCursor, None,
			_("The cursor object for the currently selected key value. (dCursorMixin child)"))

	DataSource = property(_getDataSource, _setDataSource, None,
			_("The title of the cursor. Used in resolving DataSource references. (str)"))

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
 
	DefaultValues = property(_getDefaultValues, _setDefaultValues, None,
			_("""A dictionary specifying default values for fields when a new record is added.

			The values of the dictionary can be literal (must match the field type), or
			they can be a function object which will be called when the new record is added
			to the bizobj."""))

	Encoding = property(_getEncoding, _setEncoding, None,
			_("Name of encoding to use for unicode  (str)") )

	FillLinkFromParent = property(_getFillLinkFromParent, _setFillLinkFromParent, None,
			_("""In the onNew() method, do we fill in the foreign key field specified by the
			LinkField property with the value returned by calling the bizobj's 	getParentPK() 
			method? (bool)"""))

	IsAdding = property(_isAdding, None, None,
			_("Returns True if the current record is new and unsaved."))

	KeyField = property(_getKeyField, _setKeyField, None,
			_("""Name of field that is the PK. If multiple fields make up the key,
			separate the fields with commas. (str)"""))

	LastSQL = property(_getLastSQL, None, None,
			_("Returns the last executed SQL statement."))

	LinkField = property(_getLinkField, _setLinkField, None,
			_("Name of the field that is the foreign key back to the parent. (str)"))

	NewChildOnNew = property(_getNewChildOnNew, _setNewChildOnNew, None,
			_("Should new child records be added when a new parent record is added? (bool)"))

	NewRecordOnNewParent = property(_getNewRecordOnNewParent, _setNewRecordOnNewParent, None,
			_("If this bizobj's parent has NewChildOnNew==True, do we create a record here? (bool)"))

	NonUpdateFields = property(_getNonUpdateFields, _setNonUpdateFields, None,
			_("Fields in the cursor to be ignored during updates"))

	Parent = property(_getParent, _setParent, None,
			_("Reference to the parent bizobj to this one. (dBizobj)"))

	ParentLinkField = property(_getParentLinkField, _setParentLinkField, None,
			_("""Name of the field in the parent table that is used to determine child
			records. If empty, it is assumed that the parent's PK is used  (str)"""))

	Record = property(_getRecord, None, None,
			_("""Represents a record in the data set. You can address individual
			columns by referring to 'self.Record.fieldName' (read-only) (no type)"""))
	
	RequeryChildOnSave = property(_getRequeryChildOnSave, _setRequeryChildOnSave, None,
			_("Do we requery child bizobjs after a Save()? (bool)"))

	RequeryOnLoad = property(_getRequeryOnLoad, _setRequeryOnLoad, None,
			_("""When true, the cursor object runs its query immediately. This
			is useful for lookup tables or fixed-size (small) tables. (bool)"""))

	RequeryWithParent = property(_getRequeryWithParent, _setRequeryWithParent, None,
			_("""Specifies whether a child bizobj gets requeried automatically.

				When True (the default) moving the record pointer or requerying the
				parent bizobj will result in the child bizobj's getting requeried
				as well. When False, user code will have to manually call
				child.requery() at the appropriate time.
				"""))

	RestorePositionOnRequery = property(_getRestorePositionOnRequery, _setRestorePositionOnRequery, None,
			_("After a requery, do we try to restore the record position to the same PK?"))

	RowCount = property(_getRowCount, None, None,
			_("""The number of records in the cursor's data set. It will be -1 if the
			cursor hasn't run any successful queries yet. (int)"""))

	RowNumber = property(_getRowNumber, _setRowNumber, None,
			_("The current position of the record pointer in the result set. (int)"))

	SQL = property(_getSQL, _setSQL, None,
			_("SQL statement used to create the cursor's data. (str)"))

	SqlManager = property(_getSqlMgr, None, None,
			_("Reference to the cursor that handles SQL Builder information (cursor)") )

	UserSQL = property(_getUserSQL, _setUserSQL, None,
			_("SQL statement to run. If set, the automatic SQL builder will not be used."))

	VirtualFields = property(_getVirtualFields, _setVirtualFields, None,
			_("""A dictionary mapping virtual_field_name to function to call.

			The specified function will be called when getFieldVal() is called on 
			the specified virtual field name."""))

