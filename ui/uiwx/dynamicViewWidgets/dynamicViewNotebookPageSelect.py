import wx, wx.help
import dynamicViewBase as dynview
import dabo.classes as classes
import dynamicViewNotebookPage as page
                    
class SelectPage(page.Page):
    def __init__(self, parent):
        page.Page.__init__(self, parent, "selectPage")

    def fillItems(self):
        self.selectOptionsPanel = self._getSelectOptions()
       
        self._initEnabled()

        self.GetSizer().Add(self.selectOptionsPanel, 0, wx.GROW|wx.ALL, 5)
        
#        self.SetAutoLayout(True)
#        selectOptionsSizer.Fit(self)
        
        # need to do an initial requery:
        self.requery()
    
    def OnSelectCheckbox(self, event):
        self._setEnabled(event.GetEventObject())
    
    def _initEnabled(self):
        for optionRow in self.selectOptionsPanel.selectOptions:
            self._setEnabled(self.FindWindowById(optionRow["cbId"]))
            
    def _setEnabled(self,cb):
        # Get reference(s) to the associated input control(s)
        user1, user2 = None, None
        for optionRow in self.selectOptionsPanel.selectOptions:
            if optionRow["cbId"] == cb.GetId():
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
                if dataType == "overrideSQL":
                    user1.SetValue(self.getSQL())
            else:
                if dataType == "overrideSQL":
                    user1.SetValue("")
        except AttributeError: pass
         
        try:
            user2.Enable(cb.IsChecked())
        except AttributeError: pass
       
    def OnRefresh(self, event):
        self.requery()
    
    def getSQL(self):
        # for each checked selection item, get the where clause:
        user1, user2 = None, None
        whereClause = ""
        
        for optionRow in self.selectOptionsPanel.selectOptions:
            cb = self.FindWindowById(optionRow["cbId"])
            if cb.IsChecked() and optionRow["dataType"] <> "overrideSQL":
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
        
        viewObject = self.notebook.frame.wicket.getViewObject()
        viewObject.whereClause = whereClause
        sql = viewObject.getSQL()
#        print "getsql", sql
        return sql
        
    def getOverriddenSQL(self):
        sql = None
        for optionRow in self.selectOptionsPanel.selectOptions:
            if optionRow["dataType"] == "overrideSQL":
                if self.FindWindowById(optionRow["cbId"]).IsChecked() == True:
                    sql = self.FindWindowById(optionRow["user1Id"]).GetValue()
                break            
        return sql
        
    def requery(self):
        sql = self.getOverriddenSQL()
        if sql <> None:
            # user has overridden
            sql = sql 
        else:
            sql = self.getSQL()
        viewObject = self.notebook.frame.wicket.getViewObject()

        try:        
            self.notebook.frame.wicket.viewCursor = viewObject.viewRequery(sql,wx.GetApp().dbc)
        except:
            self.notebook.frame.wicket.viewCursor = None
        
        if self.notebook.frame.wicket.viewCursor <> None:
            statusMessage = "%i record%s selected in %s second%s" % (
                    viewObject.lastQueryTally, 
                   (viewObject.lastQueryTally == 1 and ('',) or ('s',))[0], 
                   viewObject.lastQueryTime,
                   (viewObject.lastQueryTime == 1 and ('',) or ('s',))[0])
        else:
            statusMessage = "Error getting dynamic view..."
                       
        if self.notebook.GetPageCount() > 1:  # only if the browse page exists already...
            self.notebook.GetPage(1).statusLabel.SetLabel(statusMessage)
            self.notebook.GetPage(1).grid.GetTable().fillTable() # make this raise an event instead...
            self.notebook.AdvanceSelection()
        else:
            self.notebook.setInitialStatusMessage(statusMessage)
        
    def _getSelectOptions(self):
        ''' fillSelectOptions() -> wx.Panel 
        
        Go through the dynview def, and make a
        panel of controls that represent the
        available select options. '''
        
        panel = wx.Panel(self, -1)
        frame = self.notebook.frame
        wicket = frame.wicket
        
        # panel.selectOptions is a list of dictionaries
        panel.selectOptions = []
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        label = wx.StaticText(panel, -1, "Please enter your record selection criteria:")
        label.SetHelpText("The better refined your selection criteria, the better, as "
                        "fewer network resources will have to be used to get the smaller "
                        "dataset from from the server.")
        sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        stringMatchFields = []

        for column in wicket.dynamicViews[wicket.viewName]["fields"]:
            try:
                selectTypes = column["selectTypes"]
            except KeyError:
                selectTypes = ()
            
            
            for selectType in selectTypes:
                # Id's for the UI input elements:
                cbId = wx.NewId()
                user1Id = wx.NewId()
                user2Id = wx.NewId()  # not used by all the select options but generated
                                    # and saved anyway - keeps code prettier at the minor
                                    # waste of runtime memory
                
                box = wx.BoxSizer(wx.HORIZONTAL)
                
                
                if selectType == "range":
                    where = "%s BETWEEN '?(user1)' AND '?(user2)'" % column["select"]
                        
                    cb = wx.CheckBox(panel, cbId, "&%s) %s is in the range of:" % (
                                        len(panel.selectOptions), column["caption"]))
                    
                    wx.EVT_CHECKBOX(self, cbId, self.OnSelectCheckbox)
                    
                    box.Add(cb, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

                    text = classes.TextBox(panel, user1Id)
                    box.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

                    label = wx.StaticText(panel, -1, "and")
                    box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

                    text = classes.TextBox(panel, user2Id)
                    box.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
                    
                elif selectType == "stringMatch":
                    # stringMatch gets grouped together into one selectOptions field.
                    stringMatchFields.append(column)
                    where = None
                    
                elif selectType == "startsWith":
                    where = "%s LIKE '?(user1)%c'" % (column["select"], "%")
                    
                    cb = wx.CheckBox(panel, cbId, "&%s) %s starts with:" % (
                                        len(panel.selectOptions), column["caption"]))
                    
                    wx.EVT_CHECKBOX(self, cbId, self.OnSelectCheckbox)
                    
                    box.Add(cb, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

                    text = classes.TextBox(panel, user1Id)
                    box.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
                    
                else:
                    where = None

                                                        
                if where <> None:
                    panel.selectOptions.append({"dataType": column["type"],
                                                "cbId": cbId,
                                                "user1Id": user1Id,
                                                "user2Id": user2Id})    

                    sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5)
                    panel.selectOptions[len(panel.selectOptions) - 1]["where"] = where

        # Any fielddef encountered in the above block with type of 'stringMatch'
        # got appended to the stringMatchFields list. Take this list, and define
        # one selectOptions control that will operate on all these fields.
        if len(stringMatchFields) > 0:
            where = ""

            cb = wx.CheckBox(panel, cbId, "&%s) String Match:" % (
                                len(panel.selectOptions), ))

            wx.EVT_CHECKBOX(self, cbId, self.OnSelectCheckbox)

            box.Add(cb, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

            text = classes.TextBox(panel, user1Id)
            box.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
            
            for smf in stringMatchFields:
                if len(where) > 0:
                    char = " OR "
                else:
                    char = ""
                where = ''.join((where,char,"%s LIKE '%c?(user1)%c'" % (smf["select"], "%", "%")))    

            panel.selectOptions.append({"dataType": column["type"],
                                        "cbId": cbId,
                                        "user1Id": user1Id,
                                        "user2Id": user2Id})    

            sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5)
            panel.selectOptions[len(panel.selectOptions) - 1]["where"] = where

        line = wx.StaticLine(panel, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        if wx.Platform != "__WXMSW__":
           btn = wx.help.ContextHelpButton(panel)
           box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
 
        btn = wx.Button(panel, wx.ID_OK, " &Refresh ")
        btn.SetDefault()
        btn.SetHelpText("A new recordset (browse) will be generated based on the "
                        "selection criteria you've entered.")
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        wx.EVT_BUTTON(self, wx.ID_OK, self.OnRefresh)

        # After all the other options, add a place for advanced users to override
        # the generated sql.
        cbId = wx.NewId()
        user1Id = wx.NewId()
        box = wx.BoxSizer(wx.HORIZONTAL)
        cb = wx.CheckBox(panel, cbId, "&%s) Override SQL:" % (
                                len(panel.selectOptions),))
        wx.EVT_CHECKBOX(self, cbId, self.OnSelectCheckbox)
        box.Add(cb, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        text = classes.EditBox(panel, user1Id)
        text.SetSize((80,200))
        font = text.GetFont()
        font.SetFamily(wx.TELETYPE)
        text.SetFont(font)
        box.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        panel.selectOptions.append({"dataType": "overrideSQL",
                                        "cbId": cbId,
                                        "user1Id": user1Id,
                                        "user2Id": -1})    

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5)
        

        panel.SetSizer(sizer)
        panel.SetAutoLayout(True)
        sizer.Fit(panel)
        
        return panel
        
        
