''' dPage.py '''
import wx
from dGrid import dGrid
from dControlMixin import dControlMixin
from dEditBox import dEditBox
from dTextBox import dTextBox
from dSpinner import dSpinner
from dCheckBox import dCheckBox
from dLabel import dLabel
import dMessageBox, dEvents

class dPage(wx.Panel, dControlMixin):
        
    def __init__(self, parent, name="dPage"):
        wx.Panel.__init__(self, parent, 0)
        dControlMixin.__init__(self, name)

        self.initSizer()
        self.itemsFilled = False
        
    def initSizer(self):
        ''' Set up the default vertical box sizer for the page.
        '''
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        
    def fillItems(self):
        ''' Fill the controls in the page.
        
        Called when the page is entered.
        '''
        pass
        
    def onEnterPage(self):
        ''' Occurs when this page becomes the active page.
        '''
        if not self.itemsFilled:
            self.fillItems()
            self.itemsFilled = True
        
    def onLeavePage(self):
        ''' Occurs when this page will no longer be the active page.
        '''
        pass
        
    def onValueRefresh(self, event):
        ''' Occurs when the dForm asks dControls to refresh themselves.
        
        While dPage isn't a data-aware control, this may be useful information
        to act upon.
        '''
        event.Skip()
    

class dSelectPage(dPage):
    def fillItems(self):
        self.selectOptionsPanel = self._getSelectOptionsPanel()
        self._initEnabled()
        self.GetSizer().Add(self.selectOptionsPanel, 0, wx.GROW|wx.ALL, 5)
        #self.requery()

    def OnSelectCheckbox(self, event):
        self._setEnabled(event.GetEventObject())
    
    def _initEnabled(self):
        for optionRow in self.selectOptionsPanel.selectOptions:
            self._setEnabled(self.FindWindowById(optionRow["cbId"]))
            
    def _setEnabled(self,cb):
        # Get reference(s) to the associated input control(s)
        user1, user2 = None, None
        for optionRow in self.selectOptionsPanel.selectOptions:
            if cb and optionRow["cbId"] == cb.GetId():
                user1Id = optionRow["user1Id"]
                user2Id = optionRow["user2Id"]
                user1 = self.FindWindowById(user1Id)
                user2 = self.FindWindowById(user2Id)
                dataType = optionRow["dataType"]
                break            
                
        # enable/disable the associated input control(s) based
        # on the value of cb. Set Focus to the first control if
        # the checkbox is enabled.
        try:
            user1.Enable(cb.IsChecked())
            if cb.IsChecked():
               user1.SetFocus()
        except AttributeError: 
            pass
         
        try:
            user2.Enable(cb.IsChecked())
        except AttributeError: 
            pass
       
    
    def getWhere(self):
        # for each checked selection item, get the where clause:
        user1, user2 = None, None
        whereClause = ""
        
        for optionRow in self.selectOptionsPanel.selectOptions:
            cb = self.FindWindowById(optionRow["cbId"])
            if cb.IsChecked():
                user1Val = self.FindWindowById(optionRow["user1Id"]).GetValue()
                try:
                    user2Val = self.FindWindowById(optionRow["user2Id"]).GetValue()
                except AttributeError:
                    user2Val = None
                
                whereStub = optionRow["where"]
                whereStub = whereStub.replace("?(user1)", user1Val)
                if user2Val <> None:
                    whereStub = whereStub.replace("?(user2)", user2Val)
                
                if len(whereClause) > 0:
                    whereClause = ''.join((whereClause, "\n     AND "))
                whereClause = ''.join((whereClause, "(", whereStub, ")"))
        
        return whereClause
        
        
    def requery(self):
        sqlBuilder = self.getDform().sqlBuilder
        where = self.getWhere()
        print "where:" + where            
        sqlBuilder.setWhereClause(where)
        print "sql:" + sqlBuilder.getSQL()  
        self.getDform().requery()
    
        
    def _getSelectOptionsPanel(self):
        dataSource = self.getDform().getBizobj().dataSource
        columnDefs = self.getDform().getColumnDefs(dataSource)
        panel = wx.Panel(self, -1)

        stringMatchAll = []

        # panel.selectOptions is a list of dictionaries
        panel.selectOptions = []
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        label = wx.StaticText(panel, -1, "Please enter your record selection criteria:")
        sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        for column in columnDefs:
            
            for selectType in column["selectTypes"]:
                where = None
                # Id's for the UI input elements:
                cbId = wx.NewId()
                user1Id = wx.NewId()
                user2Id = wx.NewId()

                box = wx.BoxSizer(wx.HORIZONTAL)
                
                if selectType == "range":
                    where =     "%s BETWEEN '?(user1)' AND '?(user2)'" % column["fieldName"]
                        
                    cb = wx.CheckBox(panel, cbId, "%s is in the range of:" % (
                                        column["caption"],))
                    
                    wx.EVT_CHECKBOX(self, cbId, self.OnSelectCheckbox)
                    
                    box.Add(cb, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

                    text = wx.TextCtrl(panel, user1Id)
                    box.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

                    label = wx.StaticText(panel, -1, "and")
                    box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

                    text = wx.TextCtrl(panel, user2Id)
                    box.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
                    
                elif selectType == "stringMatchAll":
                    stringMatchAll.append(column)
                    
                else:
                    where = None

                                                        
                if where != None:
                    panel.selectOptions.append({"dataType": column["type"],
                                                "cbId": cbId,
                                                "user1Id": user1Id,
                                                "user2Id": user2Id})    

                    sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5)
                    panel.selectOptions[len(panel.selectOptions) - 1]["where"] = where

        # Any fielddef encountered in the above block with type of 'stringMatchAll'
        # got appended to the stringMatchAll list. Take this list, and define
        # one selectOptions control that will operate on all these fields.
        if len(stringMatchAll) > 0:
            cbId, user1Id, user2Id = wx.NewId(), wx.NewId(), wx.NewId()
            where = ""

            cb = wx.CheckBox(panel, cbId, "String Match:")

            wx.EVT_CHECKBOX(self, cbId, self.OnSelectCheckbox)

            box.Add(cb, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

            text = wx.TextCtrl(panel, user1Id)
            box.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
            
            for column in stringMatchAll:
                if len(where) > 0:
                    char = " OR "
                else:
                    char = ""
                where = ''.join((where,char,"%s LIKE '%c?(user1)%c'" % (column["fieldName"], "%", "%")))    

            panel.selectOptions.append({"dataType": column["type"],
                                        "cbId": cbId,
                                        "user1Id": user1Id,
                                        "user2Id": user2Id})    

            sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5)
            panel.selectOptions[len(panel.selectOptions) - 1]["where"] = where

        line = wx.StaticLine(panel, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        panel.SetSizer(sizer)
        panel.SetAutoLayout(True)
        sizer.Fit(panel)
        
        return panel


        if len(stringMatchAll) > 0:        
            labelCaption = "String Match:"
            labelWidth = 150

            bs = wx.BoxSizer(wx.HORIZONTAL)

            labelAlignment = wx.ALIGN_RIGHT

            label = dLabel(self, windowStyle = labelAlignment|wx.ST_NO_AUTORESIZE)
            label.SetSize((labelWidth,-1))
            label.SetName("lblStringMatchAll")
            label.SetLabel(labelCaption)
                
            objectRef = dTextBox(self)
            objectRef.SetName("stringMatchAll")

            bs.Add(label)
            bs.Add(objectRef, 1, wx.ALL, 0)

            self.GetSizer().Add(bs, 0, wx.EXPAND)

        self.GetSizer().Layout()


class dBrowsePage(dPage):
    def __init__(self, parent):
        dPage.__init__(self, parent, "BrowsePage")
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.gridExists = False
    
    def onRowNumChanged(self, event):
        # If RowNumChanged is received AND we are the
        # active page, select the row in the grid
        pf = self.GetParent()
        if not self.gridExists:
            self.createGrid()
        if self.gridExists and pf.GetPage(pf.GetSelection()) == self:
            self.fillGrid()
        event.Skip()
    
    def onEnterPage(self):
        bizobj = self.getDform().getBizobj()
        if bizobj and bizobj.getRowCount() >= 0:
            if not self.gridExists:
                self.createGrid()
            if self.gridExists:
                self.fillGrid()
            
    def createGrid(self):
        form = self.getDform()
        bizobj = form.getBizobj()
        self.grid = dGrid(self, bizobj, form)
        self.grid.SetName("BrowseGrid")
        self.GetSizer().Add(self.grid, 1, wx.EXPAND)
        self.GetSizer().Layout()
        self.gridExists = True
        self.grid.SetFocus()

    def fillGrid(self):
        form = self.getDform()
        bizobj = form.getBizobj()
        self.grid.columnDefs = form.getColumnDefs(bizobj.dataSource)
        self.grid.fillGrid()
        
    def editRecord(self):
        # Called by the grid: user wants to edit the current row
        self.GetParent().SetSelection(2)

                
class dEditPage(dPage):
    def onEnterPage(self):
        dPage.onEnterPage(self)
        self.onValueRefresh()

    def onValueRefresh(self, event=None):
        form = self.getDform()
        bizobj = form.getBizobj()
        if bizobj and bizobj.getRowCount() >= 0:
            self.Enable(True)
        else:
            self.Enable(False)
        if event:
            event.Skip()
        
    def fillItems(self):
        dataSource = self.getDform().getBizobj().dataSource
        columnDefs = self.getDform().getColumnDefs(dataSource)
            
        for column in columnDefs:
            
            if column["showEdit"] == True:
                fieldName = column["fieldName"]
                labelCaption = "%s:" % column["caption"]
                fieldType = column["type"]
                fieldEnabled = column["editEdit"]
                
                labelWidth = 150
                
                bs = wx.BoxSizer(wx.HORIZONTAL)
                
                labelAlignment = wx.ALIGN_RIGHT

                label = dLabel(self, windowStyle = labelAlignment|wx.ST_NO_AUTORESIZE)
                label.SetSize((labelWidth,-1))
                label.SetName("lbl%s" % fieldName)
                label.SetLabel(labelCaption)
                
                if fieldType in ["M",]:
                    classRef = dEditBox
                elif fieldType in ["I",]:
                    classRef = dSpinner
                elif fieldType in ["L",]:
                    classRef = dCheckBox
                else:
                    classRef = dTextBox
                
                objectRef = classRef(self, fieldName)
                objectRef.dataSource = dataSource
                objectRef.dataField = fieldName
                objectRef.enabled = fieldEnabled
                if self.getDform().getBizobj().getRowCount() >= 0:
                    objectRef.refresh()

                if fieldType in ["M",]:
                    expandFlags = wx.EXPAND
                else:
                    expandFlags = 0
                bs.Add(label)
                bs.Add(objectRef, 1, expandFlags|wx.ALL, 0)
                        
                if fieldType in ["M",]:
                    self.GetSizer().Add(bs, 1, wx.EXPAND)
                else:
                    self.GetSizer().Add(bs, 0, wx.EXPAND)
                
        self.GetSizer().Layout()

