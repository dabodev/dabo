from dForm import dForm
from dPageFrame import dPageFrame
from dPage import *
from dMainMenuBar import *
import dIcons

class dFormDataNav(dForm):
    ''' This is a dForm but with the following added controls:
        + Navigation Menu
        + Navigation ToolBar
        + PageFrame with 3 pages by default:
            + Select : Enter sql-select criteria.
            + Browse : Browse the result set and pick an item to edit.
            + Edit   : Edit the current record in the result set.
    '''
    def __init__(self, parent=None, name="dFormDataNav", resourceString=None):
        dForm.__init__(self, parent, name, resourceString)
        
        self._columnDefs = {}
    
    def afterSetPrimaryBizobj(self):        
        self.setupToolBar()
        self.setupMenu()
        
    def afterSetPrimaryColumnDef(self):
        self.setupPageFrame()
                
    def setupToolBar(self):
        if isinstance(self, wx.MDIChildFrame):
            # Toolbar will be attached to top-level frame
            controllingFrame = self.dApp.mainFrame
        else:
            # Toolbar will be attached to this frame
            controllingFrame = self
        toolBar = wx.ToolBar(controllingFrame, -1)
        toolBar.SetToolBitmapSize((16,16))    # Needed on non-Linux platforms
        
        self._appendToToolBar(toolBar, "First", dIcons.getIconBitmap("leftArrows"),
                              self.onFirst, "Go to the first record")
            
        self._appendToToolBar(toolBar, "Prior", dIcons.getIconBitmap("leftArrow"),
                              self.onPrior, "Go to the prior record")
            
        self._appendToToolBar(toolBar, "Requery", dIcons.getIconBitmap("requery"),
                              self.onRequery, "Requery dataset")
        
        self._appendToToolBar(toolBar, "Next", dIcons.getIconBitmap("rightArrow"),
                              self.onNext, "Go to the next record")
            
        self._appendToToolBar(toolBar, "Last", dIcons.getIconBitmap("rightArrows"),
                              self.onLast, "Go to the last record")
        
        toolBar.AddSeparator()
        
        self._appendToToolBar(toolBar, "New", dIcons.getIconBitmap("blank"),
                              self.onNew, "Add a new record")
            
        self._appendToToolBar(toolBar, "Delete", dIcons.getIconBitmap("delete"),
                              self.onDelete, "Delete this record")
        
        toolBar.AddSeparator()
            
        self._appendToToolBar(toolBar, "Save", dIcons.getIconBitmap("fileSave"),
                              self.onSave, "Save changes")
    
        self._appendToToolBar(toolBar, "Cancel", dIcons.getIconBitmap("revert"),
                              self.onCancel, "Cancel changes")
        
        controllingFrame.SetToolBar(toolBar)
        toolBar.Realize()                      # Needed on non-Linux platforms
                
        
    def getMenu(self):
        menu = dForm.getMenu(self)
        
        self._appendToMenu(menu, "Set Selection Criteria\tAlt+1", 
                          self.onSetSelectionCriteria, 
                          bitmap=dIcons.getIconBitmap("checkMark"))
        self._appendToMenu(menu, "Browse Records\tAlt+2", 
                          self.onBrowseRecords, 
                          bitmap=dIcons.getIconBitmap("browse"))
        self._appendToMenu(menu, "Edit Current Record\tAlt+3", 
                          self.onEditCurrentRecord, 
                          bitmap=dIcons.getIconBitmap("edit"))
        menu.AppendSeparator()
        
        self._appendToMenu(menu, "Requery\tCtrl+R", 
                          self.onRequery, 
                          bitmap=dIcons.getIconBitmap("requery"))
        self._appendToMenu(menu, "Save Changes\tCtrl+S", 
                          self.onSave, 
                          bitmap=dIcons.getIconBitmap("fileSave"))
        self._appendToMenu(menu, "Cancel Changes", 
                          self.onCancel, 
                          bitmap=dIcons.getIconBitmap("revert"))
        menu.AppendSeparator()
        
        self._appendToMenu(menu, "Select First Record", 
                          self.onFirst, 
                          bitmap=dIcons.getIconBitmap("leftArrows"))
        self._appendToMenu(menu, "Select Prior Record\tCtrl+,", 
                          self.onPrior, 
                          bitmap=dIcons.getIconBitmap("leftArrow"))
        self._appendToMenu(menu, "Select Next Record\tCtrl+.", 
                          self.onNext, 
                          bitmap=dIcons.getIconBitmap("rightArrow"))
        self._appendToMenu(menu, "Select Last Record", 
                          self.onLast, 
                          bitmap=dIcons.getIconBitmap("rightArrows"))
        menu.AppendSeparator()
        self._appendToMenu(menu, "New Record\tCtrl+N", 
                          self.onNew, 
                          bitmap=dIcons.getIconBitmap("blank"))
        self._appendToMenu(menu, "Delete Current Record", 
                          self.onDelete, 
                          bitmap=dIcons.getIconBitmap("delete"))
        return menu
        
        
    def setupMenu(self):
        ''' Set up the navigation menu for this frame.
        
        Called whenever the primary bizobj is set or whenever this
        frame receives the focus.
        '''
        mb = self.GetMenuBar()

        menuIndex = mb.FindMenu("&Navigation")
        if menuIndex < 0:
            menuIndex = mb.GetMenuCount()-1
            if menuIndex < 0:
                menuIndex = 0
            
            ### The intent is for the Navigation menu to be positioned before
            ### the Help menu, but it isn't working. No matter what I set for
            ### menuIndex, the nav menu always appears at the end.
            mb.Insert(menuIndex, self.getMenu(), "&Navigation")
         
                
    def setupPageFrame(self):
        ''' Set up the select/browse/edit/n pageframe.
        
        Default behavior is to set up a 3-page pageframe with 'Select', 
        'Browse', and 'Edit' pages. User may override and/or extend in 
        subclasses and overriding self.beforeSetupPageFrame(), 
        self.setupPageFrame, and/or self.afterSetupPageFrame().
        '''
        if self.beforeSetupPageFrame():
            self.pageFrame = dPageFrame(self)
            nbSizer = wx.NotebookSizer(self.pageFrame)
            self.GetSizer().Add(nbSizer, 1, wx.EXPAND)
            self.afterSetupPageFrame()
        
    def beforeSetupPageFrame(self): return True
    def afterSetupPageFrame(self): pass

    def onSetSelectionCriteria(self, event):
        ''' Occurs when the user chooses to set the selection criteria.
        '''
        self.pageFrame.SetSelection(0)
        
    def onBrowseRecords(self, event):
        ''' Occurs when the user chooses to browse the record set.
        '''
        self.pageFrame.SetSelection(1)
        
    def onEditCurrentRecord(self, event):
        ''' Occurs when the user chooses to edit the current record.
        '''
        self.pageFrame.SetSelection(2)
            
    
    def getColumnDefs(self, dataSource):
        ''' Get the column definitions for the given data source.
        
        The column definitions provide information to the data navigation
        form to smartly construct the SQL statement, the browse grid, and 
        the edit form.
        
        Return the column definitions for the given dataSource,
        or an empty list if not found. Each item in the list represents
        a column, with the following keys defining column behavior:
            
            'tableName'   : The table name that contains the field.
                            (string) (required)
                            
            'fieldName'   : The field name in the bizobj.
                            (string) (required)
                                
            'caption'     : The column header caption - used in the browse 
                            grid and as a default label for the items in 
                            the edit page. 
                            (string) (default: 'name')
                                
            'type'        : The data type in xBase notation (C,I,N,D,T) 
                            (char) (Required)
                              
            'showGrid'    : Show column in the browse grid?
                            (boolean) (default: True)
                                
            'showEdit'    : Show field in the edit page?
                            (boolean) (default: True)
                                
            'editEdit'    : Allow editing of the field in the edit page?
                            (boolean) (default: True)
                                
            'selectTypes' : List of types of select queries that can be run
                            for the field. If supplied, the field will have
                            input field(s) automatically set up in the 
                            pageframe's select page, so the user can enter
                            the criteria. If not supplied, the user will not
                            automatically be able to enter selection criteria.
                            (list) (default: fields with 'C' will get an entry
                            for selectType of 'stringMatchAll')
                                
                            The currently-supported selectTypes are:
                                
                                + range: allow user to specify a high and a
                                         low value.
                                             
                                + value: user sets an explicit value.
                                    
                                + stringMatch: user enters a string, and the field
                                               is searched for occurances of that
                                               string (SQL LIKE with '%' appended
                                               and prepended).
                                                   
                                + stringMatchAll: Like stringMatch but instead of
                                                  the data field getting its own
                                                  input field, all data fields with
                                                  stringMatchAll share one input
                                                  field on the select page.
                                                      
        Use dformDataNav.setColumnDefs() to set the definitions.
        '''
        try:
            columnDefs = self._columnDefs[dataSource]
        except KeyError:
            columnDefs = []
        return columnDefs

                
    def setColumnDefs(self, dataSource, columnDefs):
        ''' Set the grid column definitions for the given data source.
        
        See getGridColumnDefs for more explanation.
        ''' 
        
        # Make sure unspecified items get default values or if 
        # the item is required don't set the columndefs.
        for column in columnDefs:
            if not column.has_key('tableName'):
                raise KeyError, "Column definition must include a table name."
            if not column.has_key('fieldName'):
                raise KeyError, "Column definition must include a field name."
            if not column.has_key('caption'):
                column['caption'] = column['name']
            if not column.has_key('type'):
                raise KeyError, "Column definition must include a data type."
            if not column.has_key('showGrid'):
                column['showGrid'] = True
            if not column.has_key('showEdit'):
                column['showEdit'] = True
            if not column.has_key('editEdit'):
                column['editEdit'] = True
            if not column.has_key('selectTypes'):
                column['selectTypes'] = []
                if column['type'] in ('C', 'M'):
                    # column is string: add to stringMatchAll:
                    column['selectTypes'].append('stringMatchAll')
        
        self._columnDefs[dataSource] = columnDefs
        if dataSource == self.getBizobj().dataSource:
            self.afterSetPrimaryColumnDef()
        
        
    def OnSetFocus(self, event):
        ''' Occurs when the form receives the focus.
        
        For dFormDataNav, the toolbar and menu need to be set up.
        '''
        if isinstance(self, wx.MDIChildFrame):
            self.setupToolBar()
            self.setupMenu()
        event.Skip()

        
    def onRequery(self, event):
        ''' Override the dForm behavior by running the requery through the select page.
        '''
        self.pageFrame.GetPage(0).requery()
        
    
    def afterNew(self):
        ''' dForm will call this after a new record has been successfully added.
        
        Make the edit page active, as a convenience to the user.
        '''
        self.pageFrame.SetSelection(2)
