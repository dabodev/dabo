''' dFormDataNav.py

'''
from dForm import dForm
from dPageFrame import dPageFrame
from dPage import *

class dFormDataNav(dForm):
    def __init__(self, parent=None, name="dFormDataNav", resourceString=None):
        dForm.__init__(self, parent, name, resourceString)
        
        self._gridColumnDefs = {}
        self.setupPageFrame()
        self.addVCR()
    
    def _appendToMenu(self, menu, caption, function):
        menuId = wx.NewId()
        menu.Append(menuId, caption)
        wx.EVT_MENU(self, menuId, function)
        
    def getMenu(self):
        menu = dForm.getMenu(self)
        
        self._appendToMenu(menu, "Set Selection Criteria\tAlt+1", 
                          self.onSetSelectionCriteria)
        self._appendToMenu(menu, "Browse Records\tAlt+2", 
                          self.onBrowseRecords)
        self._appendToMenu(menu, "Edit Current Record\tAlt+3", 
                          self.onEditCurrentRecord)
        menu.AppendSeparator()
        
        self._appendToMenu(menu, "Requery\tCtrl+R", 
                          self.onRequery)
        self._appendToMenu(menu, "Save Changes\tCtrl+S", 
                          self.onSave)
        self._appendToMenu(menu, "Cancel Changes", 
                          self.onCancel)
        menu.AppendSeparator()
        
        self._appendToMenu(menu, "Select First Record", 
                          self.onFirst)
        self._appendToMenu(menu, "Select Prior Record\tCtrl+,", 
                          self.onPrior)
        self._appendToMenu(menu, "Select Next Record\tCtrl+.", 
                          self.onNext)
        self._appendToMenu(menu, "Select Last Record", 
                          self.onLast)
        menu.AppendSeparator()
        self._appendToMenu(menu, "New Record\tCtrl+N", 
                self.onNew)
        self._appendToMenu(menu, "Delete Current Record", 
                self.onDelete)

        return menu
        
    def setupMenu(self):
        self.SetMenuBar(wx.MenuBar())
        self.GetMenuBar().Append(self.getMenu(), "&Navigation")
        wx.EVT_MENU_OPEN(self, self.onOpenMenu)
        
    def onOpenMenu(self, event):
        menu = event.GetEventObject()
        if self.bizobjs[self.getPrimaryBizobj()].getRowCount() < 0:
            # disable all menu items except for Requery. (I'd like
            # to get some sort of "skip for" functionality build into 
            # our menus, but that will wait.).
            for item in menu.GetMenuItems():
                if item.GetText() != "Requery":
                    item.Enable(False)
        else:
            # Enable all menu items
            for item in menu.GetMenuItems():
                item.Enable(True)            

    def setupPageFrame(self):
        ''' dFormDataNav.setupPageFrame() -> 
        
            Default behavior is to set up a 3-page pageframe
            with 'Select', 'Browse', and 'Edit' pages.
            User may override and/or extend in subclasses
            and overriding self.beforeSetupPageFrame(), 
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
        self.pageFrame.SetSelection(0)
        
    def onBrowseRecords(self, event):
        self.pageFrame.SetSelection(1)
        
    def onEditCurrentRecord(self, event):
        self.pageFrame.SetSelection(2)
            
    def addVCR(self):
        ''' dForm.addVCR() -> None
        
            Add a VCR data nav control to the form -- temporary
            until we get dToolbar working.
        '''
        bs = wx.BoxSizer(wx.HORIZONTAL)
        import dVCR

        vcr = dVCR.dVCR(self)
        bs.Add(vcr, 1, wx.ALL, 0)
        self.GetSizer().Add(bs, 0, wx.EXPAND)
        self.GetSizer().Layout()

    def getGridColumnDefs(self, dataSource):
        ''' dForm.getGridColumnDefs(dataSource) -> List of Dictionaries
        
            Return the grid column definitions for the given dataSource,
            or the empty List if not found. Each dictionary in the list
            represents a column in the grid, and needs to have the 
            following keys at a minimum:
            
                'name'    : The field name in the bizobj
                'caption' : The column header caption
                'type'    : The data type in FoxPro notation (C,I,N,D,T)
            
            Use setGridColumnDefs to set the definitions.
        '''
        try:
            columnDefs = self._gridColumnDefs[dataSource]
        except KeyError:
            columnDefs = []
        return columnDefs
        
    def setGridColumnDefs(self, dataSource, columnDefs):
        ''' dForm.setGridColumnDefs(string, list) -> None
        
            Set the grid column definitions for the given dataSource.
            See getGridColumnDefs for more explanation.
        ''' 
        self._gridColumnDefs[dataSource] = columnDefs
        
