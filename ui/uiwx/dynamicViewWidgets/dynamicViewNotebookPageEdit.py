import wx
import dynamicViewBase as dynview
import dabo.classes as classes
import dynamicViewNotebookPage as page
                    
class EditPage(page.Page):
    '''Subclass this one for your custom pages.'''
    def __init__(self, parent, wicket):
        self.wicket = wicket
        page.Page.__init__(self, parent, "editPage")
        self.SetWindowStyle(wx.TAB_TRAVERSAL)
        
    def fillItems(self):
        ''' For every item in the dynview def that is defined as editable,
            create a label and an object, named with the dynview's field name.
            So, if there is an editable field named 'cdescrp', make a Label 
            with the name 'lblcdescrp', and a TextBox with the name of 'cdescrp'.
            
            Save all this to the self.objectMap list of dictionaries.
            
        '''
        
        self.objectMap = []
        wicket = self.wicket
        for fieldDef in wicket.dynamicViews[wicket.viewName]["fields"]:
            try:
                showEdit = fieldDef["showEdit"]
            except KeyError:
                showEdit = True
                
            if showEdit:
                try: 
                    name = fieldDef["name"]
                except KeyError: 
                    name = "unknown"
                
                try:
                    caption = "%s:" % fieldDef["caption"]
                except KeyError:
                    caption = "%s:" % name
                
                try:
                    fieldType = fieldDef["type"]
                except KeyError:
                    fieldType = "C"
                
                try:
                    fieldEditEnabled = fieldDef["editEnabled"]
                except KeyError:
                    fieldEditEnabled = True
                
                labelWidth = 150
                
                bs = wx.BoxSizer(wx.HORIZONTAL)
                
                labelAlignment = wx.ALIGN_RIGHT

                label = classes.Label(self, windowStyle = labelAlignment|wx.ST_NO_AUTORESIZE,
                                        size = (labelWidth, -1))
                label.SetName("lbl%s" % name)
                label.SetLabel(caption)
                
                if fieldType in ["M",]:
                    objectType = classes.EditBox
                elif fieldType in ["I",]:
                    objectType = classes.Spinner
                else:
                    objectType = classes.TextBox
                
                object = objectType(self)
                object.Enable(fieldEditEnabled)

                classes.common.EVT_FIELDCHANGED(object, object.GetId(), self.onFieldChanged)
                
                if fieldType in ["M",]:
                    expandFlags = wx.EXPAND
                else:
                    expandFlags = 0
                bs.Add(label)
                bs.Add(object, 1, expandFlags|wx.ALL, 0)
                        
                self.objectMap.append({"Id": object.GetId(), "Name": name})
                object.SetName(name)
                
                if fieldType in ["M",]:
                    self.GetSizer().Add(bs, 1, wx.EXPAND)
                else:
                    self.GetSizer().Add(bs, 0, wx.EXPAND)
                
        self.GetSizer().Layout()
        
    def onFieldChanged(self, evt):
        objectId = evt.GetId()
        objectRef = self.FindWindowById(objectId)
        fieldName = objectRef.GetName()
        fieldValue = objectRef.GetValue()
        pk = self.record.iid
        wicket = self.wicket
        
        try:
            tableName = wicket.dynamicViews[wicket.viewName]["updateTableName"]
        except KeyError:
            tableName = None
        
        if tableName == None:
            print "WARNING: Backend not being updated because you haven't defined an updateTableName."
        else:
        
            sql = " update %s set %s='%s' where iid = %s " % (tableName,
                                                        fieldName,
                                                        str(fieldValue).replace("'", "\\'"),
                                                        pk)
            wx.GetApp().dbc.dbCommand(sql)

            exec("self.record.%s = fieldValue" % (fieldName, ))

            wicket.fillGrid()
            
    def onLeavePage(self):
        # Like VFP's ActiveControlValid()
        count = 0
        for object in self.objectMap:
            objectRef = self.FindWindowById(object["Id"])
            objectRef.SetFocus()
            if count > 0:
                break
            count += 1
        
    def onEnterPage(self):
        record = self.wicket.getRecord()
        if type(record) == type(None):
            self.Enable(False)
            for object in self.objectMap:
                objectRef = self.FindWindowById(object["Id"])
                try:
                    objectRef.SetValue('')
                except TypeError:   # spinner
                    objectRef.SetValue(0)
        else:
            self.Enable(True)
            self.record = record
            focusSet = False
            for object in self.objectMap:
                objectRef = self.FindWindowById(object["Id"])
            
                # Set the control's value to that of the record.
                objectRef.SetValue(eval("record.%s" % object["Name"]))
                
                # Without the below code, focus goes to the first control
                # which could very well be disabled. This code forces focus
                # to the first enabled control.
                if not focusSet:
                    if objectRef.IsEnabled():
                        objectRef.SetFocus()
                        focusSet = True
  
