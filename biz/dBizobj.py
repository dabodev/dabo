import dabo.dConstants as k
import dabo.db.dConnection as dConnection
from dabo.db.dCursorMixin import dCursorMixin
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
        parent record. If the record set is already at the beginning, 
        return k.FILE_BOF. 
        """
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
        """ 
        Move the record pointer in the cursor back one position in the 
        result set. Update any child bizobjs to reflect the new current 
        parent record. If the record set is already at the beginning, 
        return k.FILE_BOF. 
        """
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
        """ 
        Moves the record pointer in the cursor to the next record of the result set.
        Updates any child bizobjs to reflect the new current parent record.
        If the recordset is already at the last record, returns k.FILE_EOF. 
        """
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
        """ 
        Moves the record pointer in the cursor to the last record of the result set.
        Updates any child bizobjs to reflect the new current parent record.
        If the recordset is already at the last record, returns k.FILE_EOF. 
        """
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

    def save(self, startTransaction=False, allRows=False, topLevel=True):
        """ 
        Saves any changes that have been made to the cursor.
        If the save is successful, calls the save() of all child bizobjs. 
        """
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
            for child in self.__children:
                if child.isChanged():
                    # No need to start another transaction. And since this is a child bizobj, 
                    # we need to save all rows that have changed.
                    ret = child.save(startTransaction=True, allRows=True, topLevel=False)

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


    def cancel(self, allRows=False):
        """ 
        Cancels any changes to the data. Reverts back to the orginal values
        that were in the data. 
        """
        self._errorMsg = ""

        if not self.beforeCancel():
            return k.FILE_CANCEL

        # Tell the cursor to cancel any changes
        ret = self._cursor.cancel(allRows)

        if ret == k.FILE_OK:
            # Tell each child to cancel themselves
            for child in self.__children:
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

        if not self.beforeDelete() or not self.beforePointerMove():
            return k.FILE_CANCEL

        if self.deleteChildLogic == k.REFINTEG_RESTRICT:
            # See if there are any child records
            for child in self.__children:
                if child.getRowCount() > 0:
                    self.addToErrorMsg("Deletion prohibited - there are related child records.")
                    return k.FILE_CANCEL                    

        ret = self._cursor.delete()

        if ret == k.FILE_OK:
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

            self.setMemento()
        else:
            self.addToErrorMsg(self._cursor.getErrorMsg())

        self.afterPointerMove(ret)
        self.afterChange(ret)
        self.afterDelete(ret)
        return ret


    def deleteAll(self):
        """ 
        Iterate through all the rows in the bizobj's cursor, deleting 
        each one-by-one
        """
        ret = k.FILE_OK
        while self._cursor.getRowCount() > 0:
            self.first()
            ret = self.delete()
            if ret != k.FILE_OK:
                break
        return ret


    def new(self):
        """ 
        Creates a new record, and populates it with any default 
        values specified. 
        """
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
                for child in self.__children:
                    if child.newRecordOnNewParent:
                        child.new()

            self.setMemento()
        else:
            self.addToErrorMsg(self._cursor.getErrorMsg())

        self.afterPointerMove(ret)
        self.afterNew(ret)
        return ret


    def requery(self):
        """ 
        Refreshes the cursor's dataset with the current values in the database, 
        given the current state of the filtering parameters 
        """
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
    
    
    def sort(self, col, ord=None):
        """ 
        Called when the data is to be sorted on a particular column
        in a particular order. All the checking on the parameters is done
        in the cursor. 
        """
        if not self._cursor.sort(col, ord):
            self.addToErrorMsg(self._cursor.getErrorMsg())
            return False
        return True


    def setParams(self, params):
        """ 
        Accepts a tuple that will be merged with the sql statement using the
        cursor's standard method for merging.
        """
#       if params != types.TupleType:
#           params = tuple(params)
        self._params = params


    def validate(self):
        """ 
        This is the method that you should customize in your subclasses
        to create checks on the data entered by the user to be sure that it 
        conforms to your business rules. 

        It is called by the Save() routine before saving any data. If this returns
        a false value, the save will be disallowed. You must return a True value 
        for data saving to proceed. 
        """
        return True


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
            return k.REQUERY_SUCCESS
        if self.beforeChildRequery():
            ret = k.REQUERY_SUCCESS
            for child in self.__children:
                ret = child.requery()
                if not ret == k.REQUERY_SUCCESS:
                    break
        else:
            # Something prevented the child requerying 
            ret = k.REQUERY_ERROR

        if ret != k.REQUERY_SUCCESS:
            self.addToErrorMsg(self._cursor.getErrorMsg())

        self.afterChildRequery(ret)
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
        """ Returns the number of records in the cursor's data set."""
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
    def afterCreateCursor(self, cursor): pass

