import dPage, dTextBox, dLabel, dEditBox, dCheckBox, dSpinner, dMessageBox, dIcons
import dPanel, dGrid, dCommandButton
import wx

class dSelectPage(dPage.dPage):

    def __init__(self, parent):
        dSelectPage.doDefault(parent, name="pageSelect")
                
    def createItems(self):
        self.selectOptionsPanel = self._getSelectOptionsPanel()
        self._initEnabled()
        self.GetSizer().Add(self.selectOptionsPanel, 0, wx.GROW|wx.ALL, 5)
        self.selectOptionsPanel.SetFocus()

        
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
        
    def onRequery(self, evt):
        self.requery()
        evt.Skip()
        
    def requery(self):
        bizobj = self.getDform().getBizobj()
        where = self.getWhere()
        bizobj.setWhereClause(where)
        
        # The bizobj will get the SQL from the sql builder:
        sql = bizobj.getSQL()
        
        print "\n\nsql:\n%s\n\n" % sql
        
        # But it won't automatically use that sql, so we set it here:
        bizobj.setSQL(sql)
        
        self.getDform().requery()
        
        if self.GetParent().GetSelection() == 0:
            # If the select page is active, now make the browse page active
            self.GetParent().SetSelection(1)
    
        
    def _getSelectOptionsPanel(self):
        dataSource = self.getDform().getBizobj().dataSource
        columnDefs = self.getDform().getColumnDefs(dataSource)
        panel = dPanel.dPanel(self)

        stringMatchAll = []

        # panel.selectOptions is a list of dictionaries
        panel.selectOptions = []
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        label = dLabel.dLabel(panel)
        label.Caption = "Please enter your record selection criteria:"
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
                    where =     "%s.%s BETWEEN '?(user1)' AND '?(user2)'" % (
                                column["tableName"], column["fieldName"])
                        
                    cb = dCheckBox.dCheckBox(panel, id=cbId)
                    cb.Caption = "%s is in the range of:" % (column["caption"],)
                    cb.Width = cb.GetTextExtent(cb.Caption)[0] + 23
                    
                    cb.Bind(wx.EVT_CHECKBOX, self.OnSelectCheckbox)
                    
                    box.Add(cb, 0, wx.ALL, 5)

                    text = dTextBox.dTextBox(panel, id=user1Id)
                    text.Value = ''
                    box.Add(text, 1, wx.ALL, 5)

                    label = dLabel.dLabel(panel)
                    label.Caption = "and"
                    box.Add(label, 0, wx.ALL, 5)

                    text = dTextBox.dTextBox(panel, id=user2Id)
                    text.Value = ''
                    box.Add(text, 1, wx.ALL, 5)
                    
                elif selectType == "value":
                    where = "%s.%s = '?(user1)'" % (
                                column["tableName"], column["fieldName"])
                        
                    cb = dCheckBox.dCheckBox(panel, id=cbId)
                    cb.Caption = "%s is equal to:" % (column["caption"],)
                    cb.Width = cb.GetTextExtent(cb.Caption)[0] + 23
                    
                    cb.Bind(wx.EVT_CHECKBOX, self.OnSelectCheckbox)
                    
                    box.Add(cb, 0, wx.ALL, 5)

                    text = dTextBox.dTextBox(panel, id=user1Id)
                    text.Value = ''
                    box.Add(text, 1, wx.ALL, 5)

                elif selectType == "stringMatch":
                    where = "%s.%s LIKE '%c?(user1)%c'" % (
                            column["tableName"], column["fieldName"], "%", "%")    
                        
                    cb = dCheckBox.dCheckBox(panel, id=cbId)
                    cb.Caption = "%s contains:" % (column["caption"],)
                    cb.Width = cb.GetTextExtent(cb.Caption)[0] + 23
                    
                    cb.Bind(wx.EVT_CHECKBOX, self.OnSelectCheckbox)
                    
                    box.Add(cb, 0, wx.ALL, 5)

                    text = dTextBox.dTextBox(panel, id=user1Id)
                    text.Value = ''
                    box.Add(text, 1, wx.ALL, 5)
                
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

            cb = dCheckBox.dCheckBox(panel, id=cbId)
            cb.Caption = "String Match:"
            cb.Width = cb.GetTextExtent(cb.Caption)[0] + 23
            cb.Bind(wx.EVT_CHECKBOX, self.OnSelectCheckbox)

            box.Add(cb, 0, wx.ALL, 5)

            text = dTextBox.dTextBox(panel, id=user1Id)
            text.Value = ''
            box.Add(text, 1, wx.ALL, 5)
            
            for column in stringMatchAll:
                if len(where) > 0:
                    char = " OR "
                else:
                    char = ""
                where = ''.join((where,char,"%s.%s LIKE '%c?(user1)%c'" % (
                            column["tableName"], column["fieldName"], "%", "%")))    

            panel.selectOptions.append({"dataType": column["type"],
                                        "cbId": cbId,
                                        "user1Id": user1Id,
                                        "user2Id": user2Id})    

            sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5)
            panel.selectOptions[len(panel.selectOptions) - 1]["where"] = where

        line = wx.StaticLine(panel, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        
        requeryButton = dCommandButton.dCommandButton(panel)
        requeryButton.Caption = "&Requery"
        requeryButton.Default = True             # Doesn't work on Linux, but test on win/mac
        requeryButton.Bind(wx.EVT_BUTTON, self.onRequery)
        
        box.Add(requeryButton, 0)
        sizer.Add(box, 0, wx.GROW, 5)

        panel.SetSizer(sizer)
        panel.SetAutoLayout(True)
        sizer.Fit(panel)
        
        return panel


class dBrowsePage(dPage.dPage):

    def __init__(self, parent):
        dBrowsePage.doDefault(parent, "pageBrowse")
        
                    
    def onRowNumChanged(self, event):
        # If RowNumChanged is received AND we are the
        # active page, select the row in the grid
        pf = self.GetParent()
        if not self.itemsCreated:
            self.createItems()
        if self.itemsCreated and pf.GetPage(pf.GetSelection()) == self:
            self.fillGrid()
        
        row = self.getDform().getBizobj().getRowNumber()
        col = self.grid.GetGridCursorCol()
        self.grid.SetGridCursor(row, col)
        self.grid.MakeCellVisible(row, col)
        
        event.Skip()
    
        
    def onEnterPage(self):
        bizobj = self.getDform().getBizobj()
        if bizobj and bizobj.getRowCount() >= 0:
            if not self.itemsCreated:
                self.createItems()
            if self.itemsCreated:
                self.fillGrid()
            
                
    def createItems(self):
        form = self.getDform()
        bizobj = form.getBizobj()
        self.grid = dGrid.dGrid(self, bizobj, form)
        self.grid.SetName("BrowseGrid")
        self.GetSizer().Add(self.grid, 1, wx.EXPAND)
        self.GetSizer().Layout()
        self.itemsCreated = True

        
    def fillGrid(self):
        form = self.getDform()
        bizobj = form.getBizobj()
        self.grid.columnDefs = form.getColumnDefs(bizobj.dataSource)
        self.grid.fillGrid()
        self.GetSizer().Layout()
        for window in self.grid.GetChildren():
            window.SetFocus()
                
            
    def editRecord(self):
        # Called by the grid: user wants to edit the current row
        self.GetParent().SetSelection(2)

                
        
class dEditPage(dPage.dPage):

    def __init__(self, parent):
        dEditPage.doDefault(parent, "pageEdit")

                    
    def onEnterPage(self):
        dEditPage.doDefault()
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
        
            
    def createItems(self):
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
                
                labelStyle = wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE

                label = dLabel.dLabel(self, style=labelStyle)
                label.Name="lbl%s" % fieldName 
                label.Width = labelWidth
                label.Caption = labelCaption
                
                if fieldType in ["M",]:
                    classRef = dEditBox.dEditBox
                elif fieldType in ["I",]:
                    classRef = dSpinner.dSpinner
                elif fieldType in ["L",]:
                    classRef = dCheckBox.dCheckBox
                else:
                    classRef = dTextBox.dTextBox
                
                objectRef = classRef(self)
                objectRef.Name = fieldName
                objectRef.DataSource = dataSource
                objectRef.DataField = fieldName
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

