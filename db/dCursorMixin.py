import dabo.dConstants as k
from dabo.db.dMemento import dMemento
import types

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
    # Holds the text of any error messages generated
    __errorMsg = ""
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
    # Holds the keys in the original, unsorted order for unsorting the dataset
    __unsortedRows = []


    def __init__(self, sql="", *args, **kwargs):
        if sql:
            self.sql = sql
        _blank = {}
        __unsortedRows = []


    def setSQL(self, sql):
        self.sql = sql


    def setTable(self, table):
        self.table = table


    def setKeyField(self, kf):
        self.keyField = kf


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
        try:
            self.execute(self.sql, params)
        except:
            return k.REQUERY_ERROR
        # Add mementos to each row of the result set
        self.addMemento(-1)
        # Clear the unsorted list, and then apply the current sort
        self.__unsortedRows = []
        if self.sortColumn:
            self.sort(self.sortColumn, self.sortOrder)
        return k.REQUERY_SUCCESS
        
    
    def sort(self, col, dir=None):
        """
        Sorts the result set on the specified column in the specified order.
        If the sort direction is not specified, we cycle among Ascending, 
        Descending and no sort order.
        """
        currCol = self.sortColumn
        currOrd = self.sortOrder
        
        # Check to make sure that we have data
        if self.rowcount < 1:
            self.addToErrorMsg("No rows to sort.")
            return False
        
        # Make sure that the specified column is a column in the result set
        if not self._rows[0].has_key(col):
            self.addToErrorMsg("Invalid column specified for sort: " + col)
            return False
        
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
                    # TODO: raise the appropriate exception
                    self.addToErrorMsg("Invalid Sort direction specified: " + dir)
                    return False
        
        else:
            # Different column specified.
            if (dir is None) or not dir:
                # Start in ASC order
                newOrd = "ASC"
            else:
                if dir.upper() in ("ASC", "DESC", ""):
                    newOrd = dir.upper()
                else:
                    # TODO: raise the appropriate exception
                    self.addToErrorMsg("Invalid Sort direction specified: " + dir)
                    return False
        self.__sortRows(newCol, newOrd)
        # Save the current sort values
        self.sortColumn = newCol
        self.sortOrder = newOrd
        return True
    
    
    def __sortRows(self, col, ord):
        """
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


    def isChanged(self):
        """
        Scans all the records, and compares them with their mementos. If any
        differ, the method exits and returns True. Otherwise, it returns False.
        """
        ret = False
        if self.rowcount > 0:
            for i in range(0, self.rowcount):
                rec = self._rows[i]
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


    def getFieldVal(self, fld):
        """ Returns the value of the requested field """
        ret = None
        if self.rowcount <= 0:
            self.addToErrorMsg("No records in the data set")
        else:
            rec = self._rows[self.rownumber]
            if rec.has_key(fld):
                ret = rec[fld]
            else:
                self.addToErrorMsg("Field '" + fld + "' does not exist in the data set")
        return ret


    def setFieldVal(self, fld, val):
        """ Sets the value of the specified field """
        ret = False
        if self.rowcount <= 0:
            self.addToErrorMsg("No records in the data set")
        else:
            rec = self._rows[self.rownumber]
            if rec.has_key(fld):
                rec[fld] = val
                ret = True
            else:
                self.addToErrorMsg("Field '" + fld + "' does not exist in the data set")
        return ret


    def getRowCount(self):
        ret = -1
        if hasattr(self, "rowcount"):
            ret = self.rowcount
        return ret


    def getRowNumber(self):
        ret = -1
        if hasattr(self, "rownumber"):
            ret = self.rownumber
        return ret
        
    
    def first(self):
        """ Moves the record pointer to the first record of the recordset. """
        self.__errorMsg = ""
        ret = k.FILE_OK
        if self.rowcount > 0:
            self.rownumber = 0
        else:
            ret = k.FILE_NORECORDS
            self.addToErrorMsg("No records in data set")
        return ret


    def prior(self):
        """ Moves the record pointer back one position in the recordset. """
        self.__errorMsg = ""
        ret = k.FILE_OK
        if self.rowcount > 0:
            if self.rownumber > 0:
                self.rownumber -= 1
            else:
                ret = k.FILE_BOF
                self.addToErrorMsg("Already at the beginning of the data set.")
        else:
            ret = k.FILE_NORECORDS
            self.addToErrorMsg("No records in data set")
        return ret


    def next(self):
        """ Moves the record pointer forward one position in the recordset. """
        self.__errorMsg = ""
        ret = k.FILE_OK
        if self.rowcount > 0:
            if self.rownumber < (self.rowcount-1):
                self.rownumber += 1
            else:
                ret = k.FILE_EOF
                self.addToErrorMsg("Already at the end of the data set.")
        else:
            ret = k.FILE_NORECORDS
            self.addToErrorMsg("No records in data set")
        return ret


    def last(self):
        """ Moves the record pointer to the last record in the recordset. """
        self.__errorMsg = ""
        ret = k.FILE_OK
        if self.rowcount > 0:
            self.rownumber = self.rowcount-1
        else:
            ret = k.FILE_NORECORDS
            self.addToErrorMsg("No records in data set")
        return ret


    def save(self, allrows=False):
        """ Saves any changes to the data back to the data store """
        self.__errorMsg = ""
        ret = k.FILE_OK

        # Make sure that there is data to save
        if self.rowcount <= 0:
            self.addToErrorMsg("No data to save")
            return k.FILE_CANCEL

        # Make sure that there is a PK
        if not self.checkPK():
            self.addToErrorMsg("No primary key")
            return k.FILE_CANCEL

        if allrows:
            recs = self._rows
        else:
            recs = (self._rows[self.rownumber],)

        for rec in recs:
            updret = self.__saverow(rec)
            if updret != k.UPDATE_OK:
                ret = k.FILE_CANCEL
                self.addToErrorMsg("Save row failed: %s." % updret)
                break
        return ret


    def __saverow(self, rec):
        newrec =  rec.has_key(k.CURSOR_NEWFLAG)
        mem = rec[k.CURSOR_MEMENTO]
        diff = mem.makeDiff(rec, newrec)
        ret = k.UPDATE_OK
        if diff:
            if newrec:
                flds = ""
                vals = ""
                for kk, vv in diff.items():
                    if self.autoPopulatePK and (kk == self.keyField):
                        # we don't want to include the PK in the insert
                        continue
                    flds += ", " + kk
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
                ### TODO: MySQLdb-specific! Need to make more generic
                self.execute("select last_insert_id() as newid")
                newPKVal = self._rows[0]["newid"]
            # restore the orginal values
            self.__restoreProps()
            
            if newrec and self.autoPopulatePK:
                self.setFieldVal(self.keyField, newPKVal)
            
            if newrec:
                # Need to remove the new flag
                del rec[k.CURSOR_NEWFLAG]
            else:
                if not res:
                    ret = k.UPDATE_NORECORDS
        return ret


    def new(self):
        """ Adds a new record to the data set """
        ret = k.FILE_OK
        try:
            if not self._blank:
                self.__setStructure()
            # Copy the _blank dict to the _rows, and adjust everything accordingly
            tmprows = list(self._rows)
            tmprows.append(self._blank)
            self._rows = tuple(tmprows)
            # Adjust the rowcount and position
            self.rowcount = len(self._rows)
            self.rownumber = self.rowcount - 1
            # Add the 'new record' flag to the last record (the one we just added)
            self._rows[self.rownumber][k.CURSOR_NEWFLAG] = True
            # Add the memento
            self.addMemento(self.rownumber)
        except:
            ret = k.FILE_CANCEL
        return ret


    def cancel(self, allrows=False):
        """ Reverts any changes back to the original values """
        self.__errorMsg = ""
        ret = k.FILE_OK
        # Make sure that there is data to save
        if not self.rowcount >= 0:
            self.addToErrorMsg("No data to cancel")
            return k.FILE_CANCEL

        if allrows:
            recs = self._rows
        else:
            recs = (self._rows[self.rownumber],)

        for i in range(self.rowcount-1, -1, -1):
            rec = self._rows[i]
            if rec in recs:
                if not self.isRowChanged(rec):
                    # Nothing to cancel
                    continue
                    
                newrec =  rec.has_key(k.CURSOR_NEWFLAG)
                if newrec:
                    # Discard the record, and adjust the props
                    ret = self.delete(i)
                else:
                    ret = self.__cancelRow(rec)
                if ret != k.FILE_OK:
                    break
        return ret


    def __cancelRow(self, rec):
        mem = rec[k.CURSOR_MEMENTO]
        diff = mem.makeDiff(rec)
        if diff:
            for fld, val in diff.items():
                rec[fld] = mem.getOrigVal(fld)
        return k.FILE_OK


    def delete(self, delRowNum=None):
        ret = k.FILE_OK

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
            ret = FILE_CANCEL
        return ret


    def setDefaults(self, vals):
        """ 
        Called after a new record is added so that default values can be set.
        The 'vals' parameter is a dictionary of fields and their default values.
        The memento must be updated afterwards, since these should not count
        as changes to the original values. 
        """
        row = self._rows[self.rownumber]
        for kk, vv in vals.items():
            row[kk] = vv
        row[k.CURSOR_MEMENTO].setMemento(row)


    def addMemento(self, rownum=-1):
        """ 
        Adds a memento to the specified row. If the rownum is -1, it will
        add a memento to all rows 
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
                    tmpsql = sql + " where 1=0 "

        # We need to save and restore the cursor properties, since this query will wipe 'em out.
        self.__saveProps()
        self.execute(tmpsql)
        self.__restoreProps()

        dscrp = self.description
        for fld in dscrp:
            fldname = fld[0]
            
            ### For now, just initialize the fields to empty strings,
            ###    and let the updates take care of the type.
            self._blank[fldname] = ""
#           if fld[1] == self.STRING:
#               self._blank[fldname] = ""
#           else:
#               if fld[5]:
#                   # Float
#                   exec("self._blank[fldname] = 0." + fld[5]*"0")
#               else:
#                   # Int
#                   self._blank[fldname] = 0


    def moveToPK(self, pk):
        """ 
        Find the record in the result set (if any) whose value in the keyField
        field matches the passed value. If found, set the current position to that 
        record. If not found, set the position to the first record. 
        """
        self.rownumber = 0
        for i in range(0, len(self._rows)):
            rec = self._rows[i]
            if rec[self.keyField] == pk:
                self.rownumber = i
                break


    def checkPK(self):
        """ 
        Check to see that the field(s) specified in the keyField prop exist
        in the recordset. 
        """
        # First, make sure that there is *something* in the field
        if not self.keyField:
            self.addToErrorMsg("Cannot save; no primary key specified")
            return False

        aFields = self.keyField.split(",")
        # Make sure that there is a field with that name in the data set
        ret = True
        try:
            for fld in aFields:
                self._rows[0][fld]
        except:
            self.addToErrorMsg("Primary key field '" + fld + "' does not exist in the data set")
            ret = False
        return ret


    def makePkWhere(self, rec=None):
        """ dCursorMixin.makePkWhere(rec) --> whereClause
        
        Create the WHERE clause used for updates. Optionally
        pass in a record object, otherwise just use the 
        current rownumber.
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
        """ Creates the 'set field=val' section of an Update statement """
        ret = ""
        for fld, val in diff.items():
            if ret:
                ret += ", "
            if type(val) == types.StringType:
                ret += fld + " = " + self.__escQuote(val) + " "
            else:
                ret += fld + " = " + str(val) + " "
        return ret


    def __saveProps(self, saverows=True):
        self.holdrows = self._rows
        self.holdcount = self.rowcount
        self.holdpos = self.rownumber
        self.holddesc = self.description


    def __restoreProps(self, restoreRows=True):
        if restoreRows:
            self._rows = self.holdrows
        self.rowcount = len(self._rows)
        self.rownumber = min(self.holdpos, self.rowcount-1)
        self.description = self.holddesc


    def __escQuote(self, val):
        ret = val
        if type(val) in (types.StringType, types.UnicodeType):
            # escape and then wrap in single quotes
            sl = "\\"
            qt = "\'"
            ret = "'" + val.replace(sl, sl+sl).replace(qt, sl+qt) + "'"
        return ret          


    def addToErrorMsg(self, txt):
        """ 
        Adds the passed text to the current error message text, 
        inserting a newline if needed 
        """
        if txt:
            if self.__errorMsg:
                self.__errorMsg += "\n"
            self.__errorMsg += txt


    def getErrorMsg(self):
        return self.__errorMsg


    def isAdding(self):
        """ Returns true if the current record has the new rec flag """
        return self._rows[self.rownumber].has_key(k.CURSOR_NEWFLAG)


    def beginTransaction(self):
        """ Implement specific calls in subclasses """
        return k.FILE_OK


    def commitTransaction(self):
        """ Implement specific calls in subclasses """
        return k.FILE_OK


    def rollbackTransaction(self):
        """ Implement specific calls in subclasses """
        return k.FILE_OK
















