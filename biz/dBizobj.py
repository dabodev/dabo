import dabo.dConstants as k
import dabo.db.dConnection as dConnection
from dabo.db.dCursorMixin import dCursorMixin
from dabo.dLocalize import loc
from dabo.dError import dError
import types

class dBizobj(object):
    # Title of the cursor. Used in resolving DataSource references
    dataSource = ""
    # SQL statement used to create the cursor's data
    sql = ""
    # When true, the cursor object does not run its query immediately. This
    # is useful for parameterized queries
    noDataOnLoad = False
    # Determines if we are using a table that auto-generates its PKs.
    autoPopulatePK = True
    # Holds the tuple of params to be merged with the sql in the cursor
    _params = None
    # Reference to the cursor object 
    _cursor = None
    # Class to instantiate for the cursor object
    dCursorMixinClass = dCursorMixin
    # Reference to the parent bizobj to this one.
    _parent = None
    # Collection of child bizobjs for this
    __children = []
    # Name of field that is the PK 
    keyField = ""
    # Name of field that is the FK back to the parent
    linkField = ""
    # Holds any error messages generated during a process
    _errorMsg = ""
    # Dictionary holding any default values to apply when a new record is created
    defaultValues = {}      
    # Do we requery child bizobjs after a Save()?
    requeryChildOnSave = True
    # Should new child records be added when a new parent record is added?
    newChildOnNew = False
    # If this bizobj's parent has newChildOnNew =True, do we create a record here?
    newRecordOnNewParent = False
    # In the onNew() method, do we fill in the linkField with the value returned by calling the parent
    # bizobj's GetKeyValue() method?
    fillLinkFromParent = False
    # After a requery, do we try to restore the record position to the same PK?
    savePosOnRequery = True

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


    def __init__(self, conn, testHack=False):
        self.TESTING = testHack
        # Save the connection reference
        self._conn = conn
        if self.TESTING:
            import MySQLdb
            self.dbapiCursorClass = MySQLdb.cursors.DictCursor
        else:
            # Base cursor class : the cursor class from the db api
            self.dbapiCursorClass = self._conn.getDictCursor()
            
        if not self.createCursor():
            ##### TODO  #######
            # Need to raise an exception here!
            pass

        # Need to set this so that different instances don't mix up the references
        # contained in this list.
        self.__children = []
    
    
    def __getattr__(self, att):
        """
        Allows for directly accessing the field values of the cursor without having
        to use self.getFieldVal(fld). If there is a field whose name is the same as 
        a built-in attribute of this object, the built-in value will always be returned.
        If there is no object attribute named 'att', and no field in the cursor by that
        name, an AttributeError is raised.
        """
        ret = self.getFieldVal(att)
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
        if self._cursor is not None:
            isFld = self.setFieldVal(att, val)
        if not isFld:
            self.__dict__[att] = val
    
        
    def createCursor(self):        
        # Create the cursor that this bizobj will be using for data
        if self.beforeCreateCursor():
            cursorClass = self.getCursorClass(self.dCursorMixinClass, self.dbapiCursorClass)
            
            if self.TESTING:
                self._cursor = self._conn.cursor(cursorclass=cursorClass)
            else:
                self._cursor = self._conn.getConnection().cursor(cursorclass=cursorClass)
            self._cursor.setSQL(self.sql)
            self._cursor.setKeyField(self.keyField)
            self._cursor.setTable(self.dataSource)
            self._cursor.setAutoPopulatePK(self.autoPopulatePK)
            if not self.noDataOnLoad:
                self._cursor.requery()
            self.afterCreateCursor(self._cursor)

        if not self._cursor:
            return False
        return True

                    
    def getCursorClass(self, main, secondary):
        class cursorMix(main, secondary):
            superMixin = main
            superCursor = secondary
            def __init__(self, *args, **kwargs):
                if hasattr(main, "__init__"):
                    apply(main.__init__,(self,) + args, kwargs)
                    #main.__init__(self)
                if hasattr(secondary, "__init__"):
                    apply(secondary.__init__,(self,) + args, kwargs)
        return  cursorMix


    def first(self):
        """ 
        Move the record pointer in the cursor to the first record of the 
        result set. Update any child bizobjs to reflect the new current 
        parent record. If there are no records in the data set, an exception
        will be raised.
        """
        if not self.beforeFirst() or not self.beforePointerMove():
            return False
        
        try:
            self._cursor.first()
            self.requeryAllChildren()
        except dError, e:
            # Pass the error back to the UI
            raise dError, e
            return False

        self.afterPointerMove()
        self.afterFirst()
        return True


    def prior(self):
        """ 
        Move the record pointer in the cursor back one position in the 
        result set. Update any child bizobjs to reflect the new current 
        parent record. If there are no records in the data set, an exception
        will be raised. 
        """
        if not self.beforePrior() or not self.beforePointerMove():
            return False
        
        try:
            self._cursor.prior()
            self.requeryAllChildren()
        except dError, e:
            # Pass the error back to the UI
            raise dError, e
            return False

        self.afterPointerMove()
        self.afterPrior()
        return True


    def next(self):
        """ 
        Moves the record pointer in the cursor to the next record of the result set.
        Updates any child bizobjs to reflect the new current parent record.
        If there are no records in the data set, an exception will be raised. 
        """
        if not self.beforeNext() or not self.beforePointerMove():
            return False
        
        try:
            self._cursor.next()
            self.requeryAllChildren()
        except dError, e:
            # Pass the error back to the UI
            raise dError, e
            return False

        self.afterPointerMove()
        self.afterNext
        return True


    def last(self):
        """ 
        Moves the record pointer in the cursor to the last record of the result set.
        Updates any child bizobjs to reflect the new current parent record.
        If there are no records in the data set, an exception will be raised. 
        """
        if not self.beforeLast() or not self.beforePointerMove():
            return False
        
        try:
            self._cursor.last()
            self.requeryAllChildren()
        except dError, e:
            # Pass the error back to the UI
            raise dError, e
            return False

        self.afterPointerMove()
        self.afterLast()
        return True


    def save(self, startTransaction=False, allRows=False, topLevel=True):
        """ 
        Saves any changes that have been made to the cursor.
        If the save is successful, calls the save() of all child bizobjs. 
        """
        if not self.beforeSave():
            return False
        
        try:
            # Validate any changes to the data. If there is data that fails
            # validation, an error will be raised.
            self.validate()
        except dError, e:
            return dError, e
            
        # See if we are saving a newly added record, or mods to an existing record.
        isAdding = self._cursor.isAdding()

        if startTransaction:
            # Tell the cursor to issue a BEGIN TRANSACTION command
            try:
                self._cursor.beginTransaction()
            except dError, e:
                raise dError, e

        # OK, this actually does the saving to the database
        try:
            self._cursor.save(allRows)
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
                self._cursor.commitTransaction()
            if topLevel and self.requeryChildOnSave:
                self.requeryAllChildren()

            self.setMemento()

        except dError, e:
            # Something failed; reset things.
            if startTransaction:
                self._cursor.rollbackTransaction()
            # Pass the exception to the UI
            raise dError, e

        # Two hook methods: one specific to Save(), and one which is called after any change
        # to the data (either save() or delete()).
        self.afterChange()
        self.afterSave()
        return True


    def cancel(self, allRows=False):
        """ 
        Cancels any changes to the data. Reverts back to the orginal values
        that were in the data. 
        """
        if not self.beforeCancel():
            return False

        # Tell the cursor to cancel any changes
        try:
            self._cursor.cancel(allRows)
            # Tell each child to cancel themselves
            for child in self.__children:
                child.cancel(allRows)
                child.requery()
        except dError, d:
            raise dError, d

        self.setMemento()
        self.afterCancel()
        return True


    def delete(self):
        """ Deletes the current row of data """
        if not self.beforeDelete() or not self.beforePointerMove():
            return False

        if self.deleteChildLogic == k.REFINTEG_RESTRICT:
            # See if there are any child records
            for child in self.__children:
                if child.getRowCount() > 0:
                    raise dError, loc("Deletion prohibited - there are related child records.")

        try:
            self._cursor.delete()
            if self._cursor.getRowCount() == 0:
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

        except dError, e:
            raise dError, e

        self.afterPointerMove()
        self.afterChange()
        self.afterDelete()
        return True


    def deleteAll(self):
        """ 
        Iterate through all the rows in the bizobj's cursor, deleting 
        each one-by-one
        """
        try:
            while self._cursor.getRowCount() > 0:
                self.first()
                ret = self.delete()
        except dError, e:
            raise dError, e
        return True


    def new(self):
        """ 
        Creates a new record, and populates it with any default 
        values specified. 
        """
        if not self.beforeNew() or not self.beforePointerMove():
            return False

        try:
            self._cursor.new()
            # Hook method for things to do after a new record is created.
            self.onNew()

            # Update all child bizobjs
            self.requeryAllChildren()

            if self.newChildOnNew:
                # Add records to all children set to have records created on a new parent record.
                for child in self.__children:
                    if child.newRecordOnNewParent:
                        child.new()

            self.setMemento()
            
        except dError, e:
            raise dError, e

        self.afterPointerMove()
        self.afterNew()
        return True
    
        
    def getSQL(self):
        ''' Return the current SQL expression.'''
        return self.sql
        
        
    def setSQL(self, sql):
        """ Allows you to change the sql executed by the cursor """
        self.sql = sql
        self._cursor.setSQL(sql)


    def requery(self):
        """ 
        Refreshes the cursor's dataset with the current values in the database, 
        given the current state of the filtering parameters 
        """
        if not self.beforeRequery():
            return False

        try:
            # Hook method for creating the param list
            params = self.getParams()
    
            # Record this in case we need to restore the record position
            currPK = self.getPK()
    
            # run the requery
            self._cursor.requery(params)

            if self.savePosOnRequery:
                self.moveToPK(currPK)

            self.requeryAllChildren()
            self.setMemento()

        except dError, e:
            raise dError, e

        self.afterRequery()
        return True
    
    
    def sort(self, col, ord=None, caseSensitive=True):
        """ 
        Called when the data is to be sorted on a particular column
        in a particular order. All the checking on the parameters is done
        in the cursor. 
        """
        try:
            self._cursor.sort(col, ord, caseSensitive)
        except dError, e:
            raise dError, e
        return True


    def setParams(self, params):
        """ 
        Accepts a tuple that will be merged with the sql statement using the
        cursor's standard method for merging.
        """
        self._params = params


    def validate(self, allrows=True):
        """ 
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
                self.moveToRowNum(i)
                if self.isChanged():
                    # No need to validate if the data hasn't changed
                    self.validateRecord()
            self.moveToRowNum(currRow)
        except dError, e:
            # First try to return to the original row, if possible
            try:
                self.moveToRowNum(currRow)
            except: pass
            raise dError, e
    
    
    def validateRecord(self):
        """
        This is the method that you should customize in your subclasses
        to create checks on the data entered by the user to be sure that it 
        conforms to your business rules. Your validation code should raise
        an instance of dError, and pass the explanatory text for the failure
        as the exception's argument. Example:
            
            if not myfield = somevalue:
                raise dError, "MyField must be equal to SomeValue"

        It is assumed that we are on the correct record for testing before
        this method is called.
        """
        pass
    
    
    def moveToRowNum(self, rownum):
        try:
            self._cursor.moveToRowNum(rownum)
        except dError, e:
            raise dError, e


    def moveToPK(self, pk):
        try:
            self._cursor.moveToPK(pk)
        except dError, e:
            raise dError, e
    
    
    def seek(self, val, fld=None, caseSensitive=False, near=False):
        return self._cursor.seek(val, fld, caseSensitive, near)


    def isChanged(self):
        """ 
        Returns whether or not the data for the current record in the cursor has changed, or
        if the data in any child bizobjs has changed. 
        """
        ret = self._cursor.isChanged()

        if not ret:
            # see if any child bizobjs have changed
            for child in self.__children:
                ret = ret and child.isChanged()
                if ret:
                    break
        return ret


    def onDeleteLastRecord(self):
        """ 
        Hook method called when the last record of the cursor 
        has been deleted 
        """
        pass


    def onSaveNew(self):
        """ Hook method called after successfully saving a new record """
        pass
    
    
    def onNew(self):
        """ Populates the record with any default values """
        self._cursor.setDefaults(self.defaultValues)

        # Call the custom hook method
        self.onNewHook()


    def onNewHook(self):
        """ 
        Hook method called after the default values have been 
        set in onNew(). 
        """
        pass


    def addChild(self, child):
        """ 
        During the creation of the form, child bizobjs are added by the parent.
        This stores the child reference here, and sets the reference to the 
        parent in the child. 
        """
        if child not in self.__children:
            self.__children.append(child)
            child.setParent(self)


    def setParent(self, parent):
        """ Stores a reference to this object's parent bizobj. """
        self._parent = parent


    def requeryAllChildren(self):
        """ 
        Called to assure that all child bizobjs have had their data sets 
        refreshed to match the current status. 
        """
        if len(self.__children) == 0:
            return True
        if not self.beforeChildRequery():
            return False
            
        try:
            for child in self.__children:
                ret = child.requery()
        except dError, e:
            # Something prevented the child requerying 
            raise dError, e

        self.afterChildRequery()
        return True


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
        if self._cursor is not None:
            return self._cursor.getFieldVal(fld)
        else:
            return None


    def setFieldVal(self, fld, val):
        """ Sets the value of the specified field """
        if self._cursor is not None:
            return self._cursor.setFieldVal(fld, val)
        else:
            return None
    
    
    def getDataSet(self):
        """
        Returns the full data set from the cursor. Used by UI objects such as
        the grid for efficient loading of the data.
        """
        return self._cursor.getDataSet()
        


    def getParams(self):
        """ 
        This is the place to define the parameters to be used to modify
        the SQL statement used to produce the record set. If the cursor for
        this bizobj does not need parameters, leave this as is. Otherwise, 
        use this method to create a tuple to be passed to the cursor, where 
        it will be used to modify the query using standard printf syntax. 
        """
        return self._params


    def setMemento(self):
        """ 
        Tell the cursor to take a snapshot of the current state of the 
        data. This snapshot will be used to determine what, if anything, has 
        changed later on. 
        """
        self._cursor.setMemento()


    def getRowCount(self):
        """ dBizobj.getRowCount() -> int
        
            Return the number of records in the cursor's data set. This 
            will be -1 if the cursor hasn't run any successful queries
            yet.
        """
        return self._cursor.getRowCount()


    def getRowNumber(self):
        """ Returns the current row number of records in the cursor's data set."""
        return self._cursor.getRowNumber()
    
    
    def addToErrorMsg(self, txt):
        """ 
        Adds the passed text to the current error message text, 
        inserting a newline if needed 
        """
        if txt:
            if self._errorMsg:
                self._errorMsg += "\n"
            self._errorMsg += txt

    def getErrorMsg(self):
        return self._errorMsg
    
    
    def clearErrorMsg(self):
        self._errorMsg = ""
        self._cursor.clearErrorMsg()


    ########## Pre-hook interface section ##############
    def beforeNew(self): return True
    def beforeDelete(self): return True
    def beforeFirst(self): return True
    def beforePrior(self): return True
    def beforeNext(self): return True
    def beforeLast(self): return True
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
    def afterPointerMove(self): pass
    def afterSave(self): pass
    def afterCancel(self): pass
    def afterRequery(self): pass
    def afterChildRequery(self): pass
    def afterChange(self): pass
    def afterConnection(self): pass
    def afterCreateCursor(self, cursor): pass

