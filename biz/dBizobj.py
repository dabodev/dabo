import dabo.dConstants as k
import dabo.db.dConnection as dConnection
from dabo.db.dCursorMixin import dCursorMixin
from dabo.db.dSqlBuilderMixin import dSqlBuilderMixin
from dabo.dLocalize import _
import dabo.dError as dError
import dabo.common
import types

class dBizobj(dabo.common.DoDefaultMixin):
	""" The middle tier, where the business logic resides.
	"""
	
	# Class to instantiate for the cursor object
	dCursorMixinClass = dCursorMixin
	dSqlBuilderMixinClass = dSqlBuilderMixin

	##########################################
	### referential integrity stuff ####
	##########################################
	### Possible values for each type (not all are relevant for each action):
	### IGNORE - don't worry about the presence of child records
	### RESTRICT - don't allow action if there are child records
	### CASCADE - changes to the parent are cascaded to the children
	deleteChildLogic = k.REFINTEG_CASCADE       # child records will be deleted
	updateChildLogic = k.REFINTEG_IGNORE    # parent keys can be changed w/o affecting children
	insertChildLogic = k.REFINTEG_IGNORE        # child records can be inserted even if no parent record exists.
	##########################################
	# Versioning...
	_version = "0.1.0"

	# Hack so that I can test until the app can return cursorsClasses, etc.
	TESTING = False


	def __init__(self, conn, testHack=TESTING):
		""" User code should override beforeInit() and/or afterInit() instead.
		"""
		self.__cursor = None		# Reference to the cursor object. MUST be defined first.
		self._conn = conn
		self.__params = None		# tuple of params to be merged with the sql in the cursor
		self.__children = []		# Collection of child bizobjs
		
		self.beforeInit()
		
		# Dictionary holding any default values to apply when a new record is created
		# (should be made into a property - do we have a name/value editor for the propsheet?)
		self.defaultValues = {}      

		if testHack:
			import MySQLdb
			self.dbapiCursorClass = MySQLdb.cursors.DictCursor
		else:
			# Base cursor class : the cursor class from the db api
			self.dbapiCursorClass = self._conn.getDictCursor()

		if not self.createCursor():
			##### TODO  #######
			# Need to raise an exception here!
			pass

		self.afterInit()
		
		
	def beforeInit(self):
		""" Hook for subclasses.
		"""
		pass
	
	
	def afterInit(self):
		""" Hook for subclasses.
		"""
		pass
		

	def __getattr__(self, att):
		"""
		Allows for directly accessing the field values of the cursor without having
		to use self.getFieldVal(fld). If there is a field whose name is the same as 
		a built-in attribute of this object, the built-in value will always be returned.
		If there is no object attribute named 'att', and no field in the cursor by that
		name, an AttributeError is raised.
		"""
		try:
			ret = self.getFieldVal(att)
		except (dError.dError, dError.NoRecordsError):
			ret = None
		if ret is None:
			raise AttributeError, " '%s' object has no attribute '%s' " % (self.__class__.__name__, att)
		return ret


	def __setattr__(self, att, val):
		""" 
		Allows for directly setting field values as if they were attributes of the
		bizobj, rather than calling setFieldVal() for each field. If there is a field in
		the cursor with the same name as a built-in attribute of this object, the
		cursor field will be affected, not the built-in attribute.
		"""
		isFld = False
		if att != '_dBizobj__cursor' and self.__cursor is not None:
			isFld = self.setFieldVal(att, val)
		if not isFld:
			super(dBizobj, self).__setattr__(att, val)


	def createCursor(self):
		""" Create the cursor that this bizobj will be using for data.
		
		Returns True if the cursor was successfully created, and False otherwise.
		
		Subclasses should override beforeCreateCursor() and/or afterCreateCursor()
		instead of overriding this method, if possible.
		"""
		if self.beforeCreateCursor():
			cursorClass = self._getCursorClass(self.dCursorMixinClass,
					self.dbapiCursorClass, 
					self.dSqlBuilderMixinClass)

			if self.TESTING:
				self.__cursor = self._conn.cursor(cursorclass=cursorClass)
			else:
				self.__cursor = self._conn.getConnection().cursor(cursorclass=cursorClass)
			self.__cursor.setSQL(self.SQL)
			self.__cursor.setKeyField(self.KeyField)
			self.__cursor.setTable(self.DataSource)
			self.__cursor.setAutoPopulatePK(self.AutoPopulatePK)
			if self.RequeryOnLoad:
				self.__cursor.requery()
			self.afterCreateCursor(self.__cursor)

		if not self.__cursor:
			return False
		return True


	def _getCursorClass(self, main, secondary, sqlbuilder):
		class cursorMix(main, secondary, sqlbuilder):
			superMixin = main
			superCursor = secondary
			superSqlBuilder = sqlbuilder
			def __init__(self, *args, **kwargs):
				if hasattr(main, "__init__"):
					apply(main.__init__,(self,) + args, kwargs)
				if hasattr(secondary, "__init__"):
					apply(secondary.__init__,(self,) + args, kwargs)
				if hasattr(sqlbuilder, "__init__"):
					apply(sqlbuilder.__init__,(self,))
		return  cursorMix


	def first(self):
		""" Move to the first record of the data set.
		
		Any child bizobjs will be requeried to reflect the new parent record. If 
		there are no records in the data set, an exception will be raised.
		"""
		if not self.beforeFirst() or not self.beforePointerMove():
			return False

		self.__cursor.first()
		self.requeryAllChildren()

		self.afterPointerMove()
		self.afterFirst()
		return True


	def prior(self):
		""" Move to the prior record of the data set.
		
		Any child bizobjs will be requeried to reflect the new parent record. If 
		there are no records in the data set, an exception will be raised.
		"""
		if not self.beforePrior() or not self.beforePointerMove():
			return False

		self.__cursor.prior()
		self.requeryAllChildren()

		self.afterPointerMove()
		self.afterPrior()
		return True


	def next(self):
		""" Move to the next record of the data set.
		
		Any child bizobjs will be requeried to reflect the new parent record. If 
		there are no records in the data set, an exception will be raised.
		"""
		if not self.beforeNext() or not self.beforePointerMove():
			return False

		self.__cursor.next()
		self.requeryAllChildren()
		
		self.afterPointerMove()
		self.afterNext
		return True


	def last(self):
		""" Move to the last record of the data set.
		
		Any child bizobjs will be requeried to reflect the new parent record. If 
		there are no records in the data set, an exception will be raised.
		"""
		if not self.beforeLast() or not self.beforePointerMove():
			return False

		self.__cursor.last()
		self.requeryAllChildren()

		self.afterPointerMove()
		self.afterLast()
		return True


	def setRowNumber(self, rownum):
		""" Move to an arbitrary row number in the data set.
		"""
		if not self.beforeSetRowNumber() or not self.beforePointerMove():
			return False
			
		self._moveToRowNum(rownum)
		self.requeryAllChildren()
		
		self.afterPointerMove()
		self.afterSetRowNumber()
		return True
		

	def save(self, startTransaction=False, allRows=False, topLevel=True):
		""" Save any changes that have been made in the data set.
		
		If the save is successful, the save() of all child bizobjs will be
		called as well. 
		"""
		if not self.beforeSave():
			return False

		# Validate any changes to the data. If there is data that fails
		# validation, an error will be raised.
		self._validate()

		# See if we are saving a newly added record, or mods to an existing record.
		isAdding = self.__cursor.isAdding()

		if startTransaction:
			# Tell the cursor to issue a BEGIN TRANSACTION command
			self.__cursor.beginTransaction()

		# OK, this actually does the saving to the database
		try:
			self.__cursor.save(allRows)
			if isAdding:
				# Call the hook method for saving new records.
				self.onSaveNew()

			# Iterate through the child bizobjs, telling them to save themselves.
			for child in self.__children:
				if child.isChanged():
					# No need to start another transaction. And since this is a child bizobj, 
					# we need to save all rows that have changed.
					child.save(startTransaction=True, allRows=True, topLevel=False)

			# Finish the transaction, and requery the children if needed.
			if startTransaction:
				self.__cursor.commitTransaction()
			if topLevel and self.RequeryChildOnSave:
				self.requeryAllChildren()

			self.setMemento()

		except dError.dError, e:
			# Something failed; reset things.
			if startTransaction:
				self.__cursor.rollbackTransaction()
			# Pass the exception to the UI
			raise dError.dError, e

		# Two hook methods: one specific to Save(), and one which is called after any change
		# to the data (either save() or delete()).
		self.afterChange()
		self.afterSave()
		return True


	def cancel(self, allRows=False):
		""" Cancel any changes to the data set, reverting back to the original values.
		"""
		if not self.beforeCancel():
			return False

		# Tell the cursor to cancel any changes
		self.__cursor.cancel(allRows)
		# Tell each child to cancel themselves
		for child in self.__children:
			child.cancel(allRows)
			child.requery()

		self.setMemento()
		self.afterCancel()
		return True


	def delete(self):
		""" Delete the current row of the data set.
		"""
		if not self.beforeDelete() or not self.beforePointerMove():
			return False

		if self.deleteChildLogic == k.REFINTEG_RESTRICT:
			# See if there are any child records
			for child in self.__children:
				if child.getRowCount() > 0:
					raise dError.dError, _("Deletion prohibited - there are related child records.")

		self.__cursor.delete()
		if self.__cursor.getRowCount() == 0:
			# Hook method for handling the deletion of the last record in the cursor.
			self.onDeleteLastRecord()
		# Now cycle through any child bizobjs and fire their cancel() methods. This will
		# ensure that any changed data they may have is reverted. They are then requeried to
		# populate them with data for the current record in this bizobj.
		for child in self.__children:
			if self.deleteChildLogic == k.REFINTEG_CASCADE:
				child.deleteAll()
			else:
				child.cancel(allRows=True)
				child.requery()


		self.afterPointerMove()
		self.afterChange()
		self.afterDelete()
		return True


	def deleteAll(self):
		""" Delete all rows in the data set.
		"""
		while self.__cursor.getRowCount() > 0:
			self.first()
			ret = self.delete()


	def new(self):
		""" Create a new record and populate it with default values.
		 
		Default values are specified in the defaultValues dictionary. 
		"""
		if not self.beforeNew() or not self.beforePointerMove():
			return False

		self.__cursor.new()
		# Hook method for things to do after a new record is created.
		self.onNew()

		# Update all child bizobjs
		self.requeryAllChildren()

		if self.NewChildOnNew:
			# Add records to all children set to have records created on a new parent record.
			for child in self.__children:
				if child.NewRecordOnNewParent:
					child.new()

		self.setMemento()


		self.afterPointerMove()
		self.afterNew()


	def setSQL(self, sql=None):
		""" Set the SQL query that will be executed upon requery().
		
		This allows you to manually override the sql executed by the cursor. If no
		sql is passed, the SQL will get set to the value returned by getSQL().
		"""
		if sql is None:
			# sql not passed; get it from the sql mixin:
			self.SQL = self.getSQL()
		else:
			# sql passed; set it explicitly
			self.SQL = sql
		# propagate the SQL downward:
		self.__cursor.setSQL(self.SQL)


	def requery(self):
		""" Requery the data set.
		
		Refreshes the data set with the current values in the database, 
		given the current state of the filtering parameters.
		"""
		if not self.beforeRequery():
			return False

		# Hook method for creating the param list
		params = self.getParams()

		# Record this in case we need to restore the record position
		try:
			currPK = self.getPK()
		except dError.NoRecordsError:
			currPK = None

		# run the requery
		self.__cursor.requery(params)

		if self.RestorePositionOnRequery:
			self._moveToPK(currPK)

		self.requeryAllChildren()
		self.setMemento()

		self.afterRequery()
		return True


	def sort(self, col, ord=None, caseSensitive=True):
		""" Sort the rows based on values in a specified column.
		
		Called when the data is to be sorted on a particular column
		in a particular order. All the checking on the parameters is done
		in the cursor. 
		"""
		self.__cursor.sort(col, ord, caseSensitive)


	def setParams(self, params):
		""" Set the query parameters for the cursor.
		
		Accepts a tuple that will be merged with the sql statement using the
		cursor's standard method for merging.
		"""
		self.__params = params


	def _validate(self, allrows=True):
		""" Internal method. User code should override validateRecord().
		
		Validate() is called by the Save() routine before saving any data.
		If any data fails validation, an exception will be raised, and the
		Save() will not be allowed to proceed.

		By default, the entire record set is validated. If you only want to 
		validate the current record, pass False as the allrows parameter.
		"""
		ret = True
		currRow = self.getRowNumber()
		if allrows:
			recrange = range(0, self.getRowCount())
		else:
			# Just the current row
			recrange = range(currRow, currRow+1)

		try:
			for i in recrange:
				self._moveToRowNum(i)
				if self.isChanged():
					# No need to validate if the data hasn't changed
					self.validateRecord()
			self._moveToRowNum(currRow)
		except dError.dError, e:
			# First try to return to the original row, if possible
			try:
				self._moveToRowNum(currRow)
			except: pass
			raise dError.dError, e


	def validateRecord(self):
		""" Hook for subclass business rule validation code.
		
		This is the method that you should customize in your subclasses
		to create checks on the data entered by the user to be sure that it 
		conforms to your business rules. Your validation code should raise
		an instance of dError.BusinessRuleViolation, and pass the explanatory 
		text for the failure as the exception's argument. Example:

			if not myfield = somevalue:
				raise dError.BusinessRuleViolation, "MyField must be equal to SomeValue"

		It is assumed that we are on the correct record for testing before
		this method is called.
		"""
		pass


	def _moveToRowNum(self, rownum):
		""" For internal use only! Should never be called from a developer's code.
		It exists so that a bizobj can move through the records in its cursor
		*without* firing additional code.
		"""
		self.__cursor.moveToRowNum(rownum)


	def _moveToPK(self, pk):
		""" For internal use only! Should never be called from a developer's code.
		It exists so that a bizobj can move through the records in its cursor
		*without* firing additional code.
		"""
		self.__cursor.moveToPK(pk)


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
		"""
		ret = self.__cursor.seek(val, fld, caseSensitive, near)
		if ret != -1:
			if runRequery:
				self.requeryAllChildren()
				self.afterPointerMove()
		return ret


	def isChanged(self, allRows=False):
		""" Return True if data has changed in this bizobj and any children.
		
		By default, only the current record is checked. Set allRows to True to
		check all records.
		"""
		ret = self.__cursor.isChanged(allRows)

		if not ret:
			# see if any child bizobjs have changed
			for child in self.__children:
				ret = ret and child.isChanged()
				if ret:
					break
		return ret


	def onDeleteLastRecord(self):
		""" Hook called when the last record has been deleted from the data set.
		"""
		pass


	def onSaveNew(self):
		""" Hook method called after successfully saving a new record.
		"""
		pass


	def onNew(self):
		""" Populate the record with any default values.
		
		User subclasses should leave this alone and instead override onNewHook(). 
		"""
		self.__cursor.setDefaults(self.defaultValues)

		# Call the custom hook method
		self.onNewHook()


	def onNewHook(self):
		""" Hook method called after the default values have been set in onNew(). 
		"""
		pass


	def addChild(self, child):
		""" Add the passed child bizobj to this bizobj.
		
		During the creation of the form, child bizobjs are added by the parent.
		This stores the child reference here, and sets the reference to the 
		parent in the child. 
		"""
		if child not in self.__children:
			self.__children.append(child)
			child.Parent = self


	def requeryAllChildren(self):
		""" Requery each child bizobj's data set.
		
		Called to assure that all child bizobjs have had their data sets 
		refreshed to match the current master row. This will normally happen
		automatically when appropriate, but user code may call this as well
		if needed.
		"""
		if len(self.__children) == 0:
			return True
		if not self.beforeChildRequery():
			return False

		for child in self.__children:
			ret = child.requery()

		self.afterChildRequery()


	def getPK(self):
		""" Return the value of the PK field.
		"""
		return self.__cursor.getFieldVal(self.KeyField)


	def getParentPK(self):
		""" Return the value of the parent bizobjs' PK field. 
		
		Alternatively, user code can just call self.Parent.getPK().
		"""
		try:
			return self.Parent.getPK()
		except dError.NoRecordsError:
			# The parent bizobj has no records
			return None


	def getFieldVal(self, fld):
		""" Return the value of the specified field in the current row. 
		"""
		if self.__cursor is not None:
			return self.__cursor.getFieldVal(fld)
		else:
			return None


	def setFieldVal(self, fld, val):
		""" Set the value of the specified field in the current row.
		"""
		if self.__cursor is not None:
			return self.__cursor.setFieldVal(fld, val)
		else:
			return None


	def getDataSet(self):
		""" Return the full data set from the cursor. 
		
		Used by UI objects such as the grid for efficient reading of the data,
		and user code can do this as well if needed, but you'll need to keep 
		the bizobj notified of any row changes and field value changes manually.
		"""
		return self.__cursor.getDataSet()


	def getParams(self):
		""" Return the parameters to send to the cursor's execute method.
		
		This is the place to define the parameters to be used to modify
		the SQL statement used to produce the record set. If the cursor for
		this bizobj does not need parameters, leave this as is. Otherwise, 
		override this method to return a tuple to be passed to the cursor, where 
		it will be used to modify the query using standard printf syntax. 
		"""
		return self.__params


	def setMemento(self):
		""" Take a snapshot of the data in the cursor.
		
		Tell the cursor to take a snapshot of the current state of the 
		data. This snapshot will be used to determine what, if anything, has 
		changed later on. 
		
		User code should not normally call this method.
		"""
		self.__cursor.setMemento()


	def getRowCount(self):
		""" Return the number of records in the cursor's data set. 
		
		The row count will be -1 if the cursor hasn't run any successful 
		queries	yet.
		"""
		return self.__cursor.getRowCount()


	def getRowNumber(self):
		""" Return the current row number of the data set.
		"""
		return self.__cursor.getRowNumber()


	def addToErrorMsg(self, txt):
		""" Add the passed text to the current error message text.
		"""
		if txt:
			if self.ErrorMessage:
				# insert a newline
				self.ErrorMessage += "\n"
			self.ErrorMessage += txt


	def clearErrorMsg(self):
		""" Clear the current error message text.
		"""
		self.ErrorMessage = ""
		self.__cursor.clearErrorMsg()

		
	def getChildren(self):
		""" Return a tuple of the child bizobjs.
		"""
		ret = []
		for child in self.__children:
			ret.append(child)
		return tuple(ret)
		
	
	def getChildByDataSource(self, dataSource):
		""" Return a reference to the child bizobj with the passed dataSource.
		"""
		ret = None
		for child in self.getChildren():
			if child.DataSource == dataSource:
				ret = child
				break
		return ret
		
		
	########## SQL Builder interface section ##############
	def addField(self, exp):
		return self.__cursor.addField(exp)
	def addFrom(self, exp):
		return self.__cursor.addFrom(exp)
	def addGroupBy(self, exp):
		return self.__cursor.addGroupBy(exp)
	def addOrderBy(self, exp):
		return self.__cursor.addOrderBy(exp)
	def addWhere(self, exp, comp="and"):
		return self.__cursor.addWhere(exp)
	def getSQL(self):
		return self.__cursor.getSQL()
	def setFieldClause(self, clause):
		return self.__cursor.setFieldClause(clause)
	def setFromClause(self, clause):
		return self.__cursor.setFromClause(clause)
	def setGroupByClause(self, clause):
		return self.__cursor.setGroupByClause(clause)
	def setLimitClause(self, clause):
		return self.__cursor.setLimitClause(clause)
	def setOrderByClause(self, clause):
		return self.__cursor.setOrderByClause(clause)
	def setWhereClause(self, clause):
		return self.__cursor.setWhereClause(clause)



	########## Pre-hook interface section ##############
	def beforeNew(self): return True
	def beforeDelete(self): return True
	def beforeFirst(self): return True
	def beforePrior(self): return True
	def beforeNext(self): return True
	def beforeLast(self): return True
	def beforeSetRowNumber(self): return True
	def beforePointerMove(self): return True
	def beforeSave(self): return True
	def beforeCancel(self): return True
	def beforeRequery(self): return True
	def beforeChildRequery(self): return True
	def beforeConnection(self): return True
	def beforeCreateCursor(self): return True
	########## Post-hook interface section ##############
	def afterNew(self): pass
	def afterDelete(self): pass
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
	def afterConnection(self): pass
	def afterCreateCursor(self, cursor): pass


	def _getCaption(self):
		try:
			return self._caption
		except AttributeError:
			return self.DataSource
			
	
	def _setCaption(self, val):
		self._caption = str(val)
	
	
	def _getDataSource(self):
		try: 
			return self._dataSource
		except AttributeError:
			return ''
	
	def _setDataSource(self, val):
		self._dataSource = str(val)
		
		
	def _getSQL(self):
		try:
			return self._SQL
		except AttributeError:
			return ''
			
	def _setSQL(self, val):
		self._SQL = str(val)
			

	def _getRequeryOnLoad(self):
		try:
			ret = self._requeryOnLoad
		except AttributeError:
			ret = False
		return ret
			
	def _setRequeryOnLoad(self, val):
		self._requeryOnLoad = bool(val)
		
		
	def _getParent(self):
		try:
			return self._parent
		except AttributeError:
			return None
			
	def _setParent(self, val):
		print "in _setParent, reminder to check to make sure the parent descends from dBizobj."
		print "val:", val
		print "self:", self
		
		self._parent = val
			
		
	def _getAutoPopulatePK(self):
		try:
			return self._autoPopulatePK
		except AttributeError:
			return True
			
	def _setAutoPopulatePK(self, val):
		self._autoPopulatePK = bool(val)
	
	
	def _getKeyField(self):
		try:
			return self._keyField
		except AttributeError:
			return ''
			
	def _setKeyField(self, val):
		self._keyField = str(val)
	
	
	def _getLinkField(self):
		try:
			return self._linkField
		except AttributeError:
			return ''
			
	def _setLinkField(self, val):
		self._linkField = str(val)
		
	
	def _getErrorMessage(self):
		try:
			return self._errorMessage
		except AttributeError:
			return ''
			
	def _setErrorMessage(self, val):
		self._errorMessage = str(val)
		
		
	def _getRequeryChildOnSave(self):
		try:
			return self._requeryChildOnSave
		except AttributeError:
			return False
			
	def _setRequeryChildOnSave(self, val):
		self._requeryChildOnSave = bool(val)
		
			
	def _getNewRecordOnNewParent(self):
		try:
			return self._newRecordOnNewParent
		except AttributeError:
			return False
			
	def _setNewRecordOnNewParent(self, val):
		self._newRecordOnNewParent = bool(val)
		
	
	def _getNewChildOnNew(self):
		try:
			return self._newChildOnNew
		except AttributeError:
			return False
			
	def _setNewChildOnNew(self, val):
		self._newChildOnNew = bool(val)

					
	def _getFillLinkFromParent(self):
		try:
			return self._fillLinkFromParent
		except AttributeError:
			return False
			
	def _setFillLinkFromParent(self, val):
		self._fillLinkFromParent = bool(val)
		
			
	def _getRestorePositionOnRequery(self):
		try:
			return self._restorePositionOnRequery
		except AttributeError:
			return True
			
	def _setRestorePositionOnRequery(self, val):
		self._restorePositionOnRequery = bool(val)
		

	Caption = property(_getCaption, _setCaption, None,
				'The friendly title of the cursor, used in messages to the end user. (str)')
	
	DataSource = property(_getDataSource, _setDataSource, None,
				'The title of the cursor. Used in resolving DataSource references. (str)')
	
	SQL = property(_getSQL, _setSQL, None, 
				'SQL statement used to create the cursor\'s data. (str)')
	
	RequeryOnLoad = property(_getRequeryOnLoad, _setRequeryOnLoad, None, 
				'When true, the cursor object runs its query immediately. This '
				'is useful for parameterized queries. (bool)')
	
	AutoPopulatePK = property(_getAutoPopulatePK, _setAutoPopulatePK, None, 
				'Determines if we are using a table that auto-generates its PKs. (bool)')

	Parent = property(_getParent, _setParent, None,
				'Reference to the parent bizobj to this one. (dBizobj)')

	KeyField = property(_getKeyField, _setKeyField, None,
				'Name of field that is the PK. (str)')
	
	LinkField = property(_getLinkField, _setLinkField, None,
				'Name of the field that is the foreign key back to the parent. (str)')
	
	ErrorMessage = property(_getErrorMessage, _setErrorMessage, None,
				'Holds any error messages generated during a process. (str)')

	RequeryChildOnSave = property(_getRequeryChildOnSave, _setRequeryChildOnSave, None,
				'Do we requery child bizobjs after a Save()? (bool)')
				
	NewChildOnNew = property(_getNewChildOnNew, _setNewChildOnNew, None, 
				'Should new child records be added when a new parent record is added? (bool)')
	
	NewRecordOnNewParent = property(_getNewRecordOnNewParent, _setNewRecordOnNewParent, None,
				'If this bizobj\'s parent has NewChildOnNew==True, do we create a record here? (bool)')

	FillLinkFromParent = property(_getFillLinkFromParent, _setFillLinkFromParent, None,
				'In the onNew() method, do we fill in the linkField with the value returned '
				'by calling the parent bizobj\'s GetKeyValue() method? (bool)')
				
	RestorePositionOnRequery = property(_getRestorePositionOnRequery, _setRestorePositionOnRequery, None,
				'After a requery, do we try to restore the record position to the same PK?')
