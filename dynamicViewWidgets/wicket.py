''' wicket.py '''
import wx
import dynamicViewBase as dynview
import dynamicViewNotebookPageEdit as editPage
import dabo.classes as classes

class Wicket(object):
    ''' Wicket() : encapsulates view cursor behavior for dynamicFrames and child views '''
    def __init__(self, parent, parentType, viewName=None, dynamicViews=None, forceShowAllColumns=None):
        object.__init__(self)
                
        self.viewCursor             = None
        self.parent                 = parent
        self._parentType            = parentType
        self.viewName               = viewName
        self.dynamicViews           = dynamicViews
        self.forceShowAllColumns    = forceShowAllColumns
        self._gridRef               = None
        self._masterWicket          = None        
        
    def setMasterWicket(self, wicket):
        self._masterWicket = wicket
        
    def getMasterWicket(self):
        return self._masterWicket
        
    def setGridRef(self, gridRef):
        self._gridRef = gridRef
        
    def getGridRef(self):
        return self._gridRef
                
    def fillGrid(self):
        self._gridRef.GetTable().fillTable()
        self._gridRef.AutoSizeColumns(True)
        self._gridRef.ForceRefresh()

    def getViewObject(self):
        return dynview.DynamicView(self.dynamicViews[self.viewName])
    
    def getViewDef(self):
        try:
            viewdef = self.dynamicViews[self.viewName]
        except KeyError:
            viewdef = {}
        return viewdef
    
    def getUpdateTableName(self):
        viewdef = self.getViewDef()
        try:
            updateTableName = viewdef["updateTableName"]
        except KeyError:
            updateTableName = None
        return updateTableName
    
    def getCaption(self):
        viewDef = self.getViewDef()
        try:
            caption = viewDef["caption"]
        except KeyError:
            caption = self.viewName
        return caption
        
    def getRecord(self):
        ''' get the cursor row that corresponds to the grid row '''
        grid = self._gridRef
        gridRowNumber = grid.GetGridCursorRow()
        table = grid.GetTable()
        pkField = table.pkField
        if pkField <> None and grid.GetNumberRows() > 0:
            row = self.viewCursor[gridRowNumber]
            return row
        else:
            return None
    
    def editRecord(self):
        parentType = self._parentType
        if parentType == "dynamicFrame":
            self.parent.notebook.SetSelection(2) # edit page knows what to do...
        elif parentType == "childView":
            # create a modal edit page:
            editDialog = wx.Dialog(self.parent, -1, "Edit", (-1,-1), (-1,-1),wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
            bs = wx.BoxSizer(wx.VERTICAL)
            
            page = editPage.EditPage(editDialog, self)
            bs.Add(page,1,wx.EXPAND)
            
            bsButton = wx.BoxSizer(wx.HORIZONTAL)
            cmdAccept = classes.CommandButtonAccept(editDialog)
            bsButton.Add(cmdAccept)
            
            cmdCancel = classes.CommandButtonCancel(editDialog)
            bsButton.Add(cmdCancel)
            
            bs.Add(bsButton,0,wx.ALIGN_RIGHT)
            
            editDialog.SetSizer(bs)
            
            page.onEnterPage()
            editDialog.ShowModal()
            editDialog.Destroy()
        else:
            pass
            
    def getCurrentRecordLabel(self):
        ''' return a string representation of the current record '''
        record = self.getRecord()
        label = ""
        if type(record) == type(None):
            label = "None"
        else:
            for field in self.getViewDef()["fields"]:
                try:
                    show = field["showRecordLabel"]
                except KeyError:
                    show = False

                if show:
                    if len(label) == 0:
                        char = ''
                    else:
                        char = ' | '    
                    label = ''.join((label, char, str(eval("record.%s" % field["name"]))))
            if label[:-3] == ' | ':
                label = label[:-3]

            if len(label) == 0:
                label = eval("record.%s" % self.getPkField())
        return label
        
    def getCurrentKeyValue(self):
        ''' return the value of the primary key of the currently
            selected row. '''
        record = self.getRecord()
        if type(record) <> type(None):
            pkField = self.getPkField()
            return eval("record.%s" % pkField)
        else:
            return None
                     
    def getPkField(self):
        ''' Return the primary key of the cursor '''
        viewDef = self.getViewDef()
        for column in viewDef["fields"]:
            try:
                if column["pk"] == True:
                    pkField = column["name"]
                    break
            except KeyError:
                    pkField = None
        return pkField
            
    def getFkFields(self):
        ''' return a list of dictionaries with keys of  "fieldName",
                                                        "foreignFieldName" '''
        viewDef = self.getViewDef()
        fkFields = []
        for column in viewDef["fields"]:
            try:
                fkField = column["fk"]
            except:
                fkField = None
            if fkField <> None:
                fkFields.append({   "fieldName": column["select"],
                                    "foreignFieldName": fkField})
        return fkFields
    
    def newRecord(self):
        # import the packages that may need to be eval'd for default values:
        import time

        viewdef         = self.getViewDef()
        updateTableName = self.getUpdateTableName()
        pkField         = self.getPkField()
        
        # fields, values for the sql insert:        
        fields = [pkField,]
        values = [0,]
        
        # add any defaults from the definition:
        for field in viewdef["fields"]:
            try:
                defaultValue = field["defaultValue"]
            except KeyError:
                defaultValue = None
            
            if defaultValue <> None:
                fields.append(field["name"])
                values.append(eval(defaultValue))
        
        # if this wicket is a child (has a masterWicket),
        # look for and set the proper fk field to the master
        # wicket's current keyfield value:
        if self._masterWicket <> None:
            fkFields        = self.getFkFields()
            fkValue = self._masterWicket.getCurrentKeyValue()
            for field in fkFields:
                if field["foreignFieldName"] == "%s.%s" % (
                    self._masterWicket.getViewDef()["tableName"],
                    self._masterWicket.getPkField()):
                        fkName = field["fieldName"][field["fieldName"].find(".")+1:] # strip tablename
                        fields.append(fkName)
                        values.append(fkValue) 
            
        fieldString = ""
        valueString = ""
        
        for field in fields:
            if len(fieldString) == 0:
                char = ""
            else:
                char = ","
            fieldString = ''.join((fieldString, char, field))
        
        for value in values:
            if len(valueString) == 0:
                char = ""
            else:
                char = ","
            valueString = ''.join((valueString, char, "'%s'" % value))
                                 
        if updateTableName <> None and pkField <> None:
            newPk = wx.GetApp().dbc.dbInsert("insert into %s (%s) values (%s)" % (updateTableName,
                                                                            fieldString,
                                                                            valueString))
            values[0] = newPk
            grid = self._gridRef
            self.viewCursor.append(fields, values)
            grid.GetTable().fillTable()
            row = self.viewCursor.seek(pkField, newPk)
            if row > -1:
                grid.SetGridCursor(row, grid.GetGridCursorCol())
                grid.MakeCellVisible(row, grid.GetGridCursorCol())
            
            self.editRecord()
                
        else:
             print "No updateTableName or pkField. Cannot insert..."
        
       
    def deleteRecord(self):
        row             = self.getRecord()
        updateTableName = self.getUpdateTableName()
        pkField         = self.getPkField()
        grid            = self._gridRef
        gridRowNumber   = grid.GetGridCursorRow()
        
        if grid.GetNumberRows() > 0 and wx.GetApp().areYouSure("Are you sure you want "
                                "to delete record %s "
                                "\nin %s?" % (self.getCurrentRecordLabel(), updateTableName), True):
            
            wx.GetApp().dbc.dbCommand("update %s set ldeleted=1 where %s=%s" % (
                                        updateTableName,
                                        pkField,
                                        eval("row.%s" % pkField)))
            
            # delete from the cursor and grid:
            del self.viewCursor[gridRowNumber]
            grid.GetTable().fillTable()
            
