from dConstants import dConstants as k
import dConnection
import dCursorMixin

### TODO ### - Change to Gadfly
from MySQLdb import cursors

class dBizobj:
	# Title of the cursor. Used in resolving DataSource references
	dataSource = ""
	# SQL statement used to create the cursor's data
	sql = ""
	# When true, the cursor object does not run its query immediately. This
	# is useful for parameterized queries
	noDataOnLoad = 0
	# Reference to the cursor object 
	_cursor = None
	# Class to instantiate for the cursor object
	cursorMixinClass = dCursorMixin.dCursorMixin
	# Base class to instantiate for the cursor object
	### TODO ### - change to Gadfly for default
	cursorBaseClass = cursors.DictCursor
	# Reference to the parent bizobj to this one.
	_parent = None
	# Collection of child bizobjs for this
	_children = []
	# Name of field that is the PK 
	keyField = ""
	# Name of field that is the FK back to the parent
	linkField = ""
	# Holds any error messages generated during a process
	_errorMsg = ""
	# Dictionary holding any default values to apply when a new record is created
	defaultValues = {}		
	# Do we requery child bizobjs after a Save()?
	requeryChildOnSave = 1
	# Should new child records be added when a new parent record is added?
	newChildOnNew = 0
	# If this bizobj's parent has newChildOnNew =1, do we create a record here?
	newRecordOnNewParent = 0
	# In the onNew() method, do we fill in the linkField with the value returned by calling the parent
	# bizobj's GetKeyValue() method?
	fillLinkFromParent = 0
	# After a requery, do we try to restore the record position to the same PK?
	savePosOnRequery = 1
	
	##########################################
	### referential integrity stuff ####
	##########################################
	### Possible values for each type (not all are relevant for each action):
	### IGNORE - don't worry about the presence of child records
	### RESTRICT - don't allow action if there are child records
	### CASCADE - changes to the parent are cascaded to the children
	deleteChildLogic = k.REFINTEG_CASCADE		# child records will be deleted
	updateChildLogic = k.REFINTEG_IGNORE	# parent keys can be changed w/o affecting children
	insertChildLogic = k.REFINTEG_IGNORE		# child records can be inserted even if no parent record exists.
	##########################################
	# Versioning...
	_version = "0.1.0"
	
	
	def __init__(self, conn):
		# Save the connection reference
		self._conn = conn
		# Now create the cursor that this bizobj will be using for data
		if self.beforeCreateCursor():
			crsClass = self.getCursorClass(self.cursorMixinClass, self.cursorBaseClass)
			self._cursor = conn.cursor(cursorclass=crsClass)
			self._cursor.setSQL(self.sql)
			self._cursor.setKeyField(self.keyField)
			self._cursor.setTable(self.dataSource)
			if not self.noDataOnLoad:
				self._cursor.requery()
			self.afterCreateCursor()
			
		if not self._cursor:
			##### TODO  #######
			# Need to raise an exception here!
			pass
	
	
	def getCursorClass(self, main, secondary):
		class result(main, secondary):
			def __init__(self, *args, **kwargs):
				if hasattr(main, "__init__"):
					apply(main.__init__,(self,) + args, kwargs)
					#main.__init__(self)
				if hasattr(secondary, "__init__"):
					apply(secondary.__init__,(self,) + args, kwargs)
		return  result
	

		
	def first(self):
		""" Moves the record pointer in the cursor to the first record of the result set.
		Updates any child bizobjs to reflect the new current parent record. 
		If the record set is already at the beginning, returns k.FILE_BOF. """
		self._errorMsg = ""
		if not self.beforeFirst() or not self.beforePointerMove():
			return k.FILE_CANCEL
		ret = self._cursor.first()
		
		if ret == k.FILE_OK:
			self.requeryAllChildren()
			self.setMemento()
		else:
			self.addToErrorMsg(self._cursor.getErrorMsg())
		self.afterPointerMove(ret)
		self.afterFirst(ret)
		return ret
	

	def prior(self):
		""" Moves the record pointer in the cursor back one position in the result set.
		Updates any child bizobjs to reflect the new current parent record. 
		If the record set is already at the beginning, returns k.FILE_BOF. """
		self._errorMsg = ""
		if not self.beforePrior() or not self.beforePointerMove():
			return k.FILE_CANCEL
		ret = self._cursor.prior()
		
		if ret == k.FILE_OK:
			self.requeryAllChildren()
			self.setMemento()
		else:
			self.addToErrorMsg(self._cursor.getErrorMsg())
		self.afterPointerMove(ret)
		self.afterPrior(ret)
		return ret
	

	def next(self):
		""" Moves the record pointer in the cursor to the next record of the result set.
		Updates any child bizobjs to reflect the new current parent record.
		If the recordset is already at the last record, returns k.FILE_EOF. """
		self._errorMsg = ""
		if not self.beforeNext() or not self.beforePointerMove():
			return k.FILE_CANCEL
		ret = self._cursor.next()
		
		if ret == k.FILE_OK:
			self.requeryAllChildren()
			self.setMemento()
		else:
			self.addToErrorMsg(self._cursor.getErrorMsg())
		self.afterPointerMove(ret)
		self.afterNext(ret)
		return ret
	

	def last(self):
		""" Moves the record pointer in the cursor to the last record of the result set.
		Updates any child bizobjs to reflect the new current parent record.
		If the recordset is already at the last record, returns k.FILE_EOF. """
		self._errorMsg = ""
		if not self.beforeLast() or not self.beforePointerMove():
			return k.FILE_CANCEL
		ret = self._cursor.last()
		
		if ret == k.FILE_OK:
			self.requeryAllChildren()
			self.setMemento()
		else:
			self.addToErrorMsg(self._cursor.getErrorMsg())
		self.afterPointerMove(ret)
		self.afterLast(ret)
		return ret
	
	def save(self, startTransaction=0, allRows=0, topLevel=1):
		""" Saves any changes that have been made to the cursor.
		If the save is successful, calls the save() of all child bizobjs. """
		self._errorMsg = ""
		
		if not self.beforeSave() or not self.validate():
			return k.FILE_CANCEL

		# See if we are saving a newly added record, or mods to an existing record.
		isAdding = self._cursor.isAdding()
		
		if startTransaction:
			# Tell the cursor to issue a BEGIN TRANSACTION command
			ret = self._cursor.beginTransaction()
			if not ret == k.FILE_OK:
				self.addToErrorMsg(self._cursor.getErrorMsg())
				return ret
		
		# OK, this actually does the saving to the database
		ret = self._cursor.save(allRows)
		
		if ret == k.FILE_OK:
			if isAdding:
				# Call the hook method for saving new records.
				self.onSaveNew()
		
			# Iterate through the child bizobjs, telling them to save themselves.
			for child in self._children:
				if child.isChanged():
					# No need to start another transaction. And since this is a child bizobj, 
					# we need to save all rows that have changed.
					ret = child.save(startTransaction=1, allRows=1, topLevel=0)
					
					if not ret == k.FILE_OK:
						self.addToErrorMsg(child.getErrorMsg())
						break

		# Finish the transaction, and requery the children if needed.
		if ret == k.FILE_OK:
			if startTransaction:
				self._cursor.commitTransaction()
			if topLevel and self.requeryChildOnSave:
				self.requeryAllChildren()
			
			self.setMemento()
			
		else:
			# Something failed; reset things.
			if startTransaction:
				self._cursor.rollbackTransaction()
			self.addToErrorMsg(self._cursor.getErrorMsg())

		# Two hook methods: one specific to Save(), and one which is called after any change
		# to the data (either save() or delete()).
		self.afterChange(ret)
		self.afterSave(ret)
		
		return ret


	def cancel(self, allRows=0):
		""" Cancels any changes to the data. Reverts back to the orginal values
		that were in the data. """
		self._errorMsg = ""
		
		if not self.beforeCancel():
			return k.FILE_CANCEL
		
		# Tell the cursor to cancel any changes
		ret = self._cursor.cancel(allRows)
		
		if ret == k.FILE_OK:
			# Tell each child to cancel themselves
			for child in self._children:
				ret = child.cancel(allRows)
				if not ret == k.FILE_OK:
					self.addToErrorMsg(child.getErrorMsg())
					break
				ret = child.requery()
		
		if ret == k.FILE_OK:
			self.setMemento()
		else:
			self.addToErrorMsg(self._cursor.getErrorMsg())
		
		self.afterCancel(ret)
		return ret


	def delete(self):
		""" Deletes the current row of data """
		self._errorMsg = ""
		
		if not self.beforeDelete() or self.beforePointerMove():
			return k.FILE_CANCEL
		
		if self.deleteChildLogic == k.REFINTEG_RESTRICT:
			# See if there are any child records
			for child in self._children:
				if child.getRowCount() > 0:
					self.addToErrorMsg("Deletion prohibited - there are related child records.")
					return k.FILE_CANCEL					
		
		ret = self._cursor.delete()
### TODO - add this logic to the cursor's Delete
# 		* If adding a new record, just revert it.
# 		IF IsAdding(This.cAlias)
# 			lnRetVal = This.oBehavior.Cancel()

		if ret == k.FILE_OK:
			if self._cursor.rowcount == 0:
				# Hook method for handling the deletion of the last record in the cursor.
				self.onDeleteLastRecord()
			# Now cycle through any child bizobjs and fire their cancel() methods. This will
			# ensure that any changed data they may have is reverted. They are then requeried to
			# populate them with data for the current record in this bizobj.
			for child in self._children:
				if self.deleteChildLogic == k.REFINTEG_CASCADE:
					child.deleteAll()
				else:
					child.cancel(allRows=1)
					child.requery()
			
			self.setMemento()
		else:
			self.addToErrorMsg(self._cursor.getErrorMsg())

		self.afterPointerMove(ret)
		self.afterChange(ret)
		self.afterDelete(ret)
		return ret
		
	
	def deleteAll(self):
		""" Iterate through all the rows in the bizobj's cursor, deleting each one-by-one"""
		while self._cursor.rowcount > 0:
			self.first()
			ret = self.delete()
			if ret != k.FILE_OK:
				break
		return ret


	def new(self):
		""" Creates a new record, and populates it with any default values specified. """
		self._errorMsg = ""
		
		if not self.beforeNew() or not self.beforePointerMove():
			return k.FILE_CANCEL
			
		ret = self._cursor.new()
		
		if ret == k.FILE_OK:
			# Hook method for things to do after a new record is created.
			self.onNew()
			
			# Update all child bizobjs
			self.requeryAllChildren()
			
			if self.newChildOnNew:
				# Add records to all children set to have records created on a new parent record.
				for child in self._children:
					if child.newRecordOnNewParent:
						child.new()
			
			self.setMemento()
		else:
			self.addToErrorMsg(self._cursor.getErrorMsg())
		
		self.afterPointerMove(ret)
		self.afterNew(ret)
		return ret

	
	def requery(self):
		""" Refreshes the cursor's dataset with the current values in the database, 
		given the current state of the filtering parameters """
		self._errorMsg = ""
		
		if not self.beforeRequery():
			return k.FILE_CANCEL
		
		# Hook method for creating the param list
		params = self.getParams()
		
		# Record this in case we need to restore the record position
		currPK = self.getPK()
		
		# run the requery
		ret = self._cursor.requery(params)
		
		if ret == k.REQUERY_SUCCESS:
			if self.savePosOnRequery:
				self._cursor.moveToPK(currPK)
			
			ret = self.requeryAllChildren()
		
			self.setMemento()
		else:
			self.addToErrorMsg(self._cursor.getErrorMsg())
		
		self.afterRequery(ret)
		return ret
	
	
	def validate(self):
		""" This is the method that you should customize in your subclasses
		to create checks on the data entered by the user to be sure that it 
		conforms to your business rules. 
		
		It is called by the Save() routine before saving any data. If this returns
		a false value, the save will be disallowed. You must return a True value 
		for data saving to proceed. """
		return 1
		
		
	def isChanged(self):
		""" Returns whether or not the data for the current record in the cursor has changed, or
		if the data in any child bizobjs has changed. """
		ret = self._cursor.isChanged()
		
		if not ret:
			# see if any child bizobjs have changed
			for child in self._children:
				ret = ret and child.isChanged()
		
		return ret
	
	
	def onDeleteLastRecord(self):
		""" Hook method called when the last record of the cursor has been deleted """
		pass
	
	
	def onNew(self):
		""" Populates the record with any default values """
		self._cursor.setDefaultVals(self.defaultValues())
		
		# Call the custom hook method
		self.onNewHook()
	
	
	def onNewHook(self):
		""" Hook method called after the default values have been set in onNew(). """
		pass
	
	
	def addChild(self, child):
		""" During the creation of the form, child bizobjs are added by the parent.
		This stores the child reference here, and sets the reference to the parent in the child. """
		if child not in self._children:
			self._children.append(child)
			child.setParent(self)
	
	
	def setParent(self, parent):
		""" Stores a reference to this object's parent bizobj. """
		self._parent = parent
	
	
	def requeryAllChildren(self):
		""" Called to assure that all child bizobjs have had their data sets refreshed to 
		match the current status. """
		if len(self._children) == 0:
			return k.REQUERY_SUCCESS
		if self.beforeChildRequery():
			ret = k.REQUERY_SUCCESS
			for child in self._children:
				ret = child.requery()
				if not ret == k.REQUERY_SUCCESS:
					break
		else:
			# Something prevented the child requerying 
			ret = k.REQUERY_ERROR
		
		if ret != k.REQUERY_SUCCESS:
			self.addToErrorMsg(self._cursor.getErrorMsg())
			
		self.afterRequeryAllChildren()
		return ret
	
	
	def getPK(self):
		""" Returns the value of the PK field """
		return self._cursor.getFieldVal(self.keyField)


	def getParentPK(self):
		""" Returns the value of the parent bizobjs' PK. """
		if self._parent is not None:
			return self._parent.getPK()
		else:
			return None

		
	def getFieldVal(self, fld):
		""" Returns the value of the requested field """
		return self._cursor.getFieldVal(fld)
		
		
	def setFieldVal(self, fld, val):
		""" Sets the value of the specified field """
		return self._cursor.setFieldVal(fld, val)
		
		
	def getParams(self):
		""" This is the place to define the parameters to be used to modify
		the SQL statement used to produce the record set. If the cursor for
		this bizobj does not need parameters, leave this as is. Otherwise, 
		use this method to create a tuple to be passed to the cursor, where 
		it will be used to modify the query using standard printf syntax. """
		return None
	
	
	def setMemento(self):
		""" Tell the cursor to take a snapshot of the current state of the 
		data. This snapshot will be used to determine what, if anything, has 
		changed later on. """
		self._cursor.setMemento()


	def getRowCount(self):
		""" Returns the number of records in the cursor's data set."""
		return self._cursor.getRowCount()
	
	
	def addToErrorMsg(self, txt):
		""" Adds the passed text to the current error message text, 
		inserting a newline if needed """
		if txt:
			if self._errorMsg:
				self._errorMsg += "\n"
			self._errorMsg += txt

	def getErrorMsg(self):
		return self._errorMsg

		
	########## Pre-hook interface section ##############
	def beforeNew(self): return 1
	def beforeDelete(self): return 1
	def beforeFirst(self): return 1
	def beforePrior(self): return 1
	def beforeNext(self): return 1
	def beforeLast(self): return 1
	def beforePointerMove(self): return 1
	def beforeSave(self): return 1
	def beforeCancel(self): return 1
	def beforeRequery(self): return 1
	def beforeChildRequery(self): return 1
	def beforeConnection(self): return 1
	def beforeCreateCursor(self): return 1
	########## Post-hook interface section ##############
	def afterNew(self, retStatus): pass
	def afterDelete(self, retStatus): pass
	def afterFirst(self, retStatus): pass
	def afterPrior(self, retStatus): pass
	def afterNext(self, retStatus): pass
	def afterLast(self, retStatus): pass
	def afterPointerMove(self, retStatus): pass
	def afterSave(self, retStatus): pass
	def afterCancel(self, retStatus): pass
	def afterRequery(self, retStatus): pass
	def afterChildRequery(self, retStatus): pass
	def afterChange(self, retStatus): pass
	def afterConnection(self): pass
	def afterCreateCursor(self): pass

