''' dDataControlMixin.py: Provide behavior common to all 
    data-aware dControls.
'''
import wx
import dPemMixin as pm

class dDataControlMixin(pm.dPemMixin):
    ''' Provide common functionality for the data-aware controls.
    '''
    def __init__(self):
        pm.dPemMixin.__init__(self)
        
        self._oldVal = None
        self.enabled = True
        
        # Initialize runtime properties
        self.SelectOnEntry = False
        self.bizobj = None
        
                
    def initEvents(self):
        pass


    def getBlankValue(self):
        ''' Return the empty value of the control.
        '''
        if isinstance(self, wx.TextCtrl):
            return ""
        elif isinstance(self, wx.CheckBox):
            return False
        elif isinstance(self, wx.SpinCtrl):
            return 0
            
            
    def getFieldVal(self):
        ''' Ask the bizobj what the current value of the field is. 
        '''
        if not self.bizobj:
            # Ask the form for the bizobj reference, and cache for next time
            self.bizobj = self.getDform().getBizobj(self.DataSource)
        return self.bizobj.getFieldVal(self.DataField)
    
        
    def setFieldVal(self, value):
        ''' Ask the bizobj to update the field value. 
        '''
        if not self.bizobj:
            # Ask the form for the bizobj reference, and cache for next time
            self.bizobj = self.getDform().getBizobj(self.DataSource)
        return self.bizobj.setFieldVal(self.DataField, value)
        
        
    def refresh(self):
        ''' Update control's value to match the current value from the bizobj.
        '''
        if self.DataSource and self.DataField:
            try:
                self.Value = self.getFieldVal()
                self.Enabled = self.enabled
            except TypeError:
                self.Value = self.getBlankValue()
                self.Enabled = False

                            
    def onValueRefresh(self, event): 
        ''' Occurs when the field value has potentially changed.
        '''
        if self.debug:
            print "onValueRefresh received by %s" % (self.GetName(),)
        self.refresh()
        if self.SelectOnEntry and self.getDform().FindFocus() == self:
            self.selectAll()
        event.Skip()

        
    def selectAll(self):
        ''' Select all text in the control.
        '''
        self.SetInsertionPoint(1)   # Best of all worlds (really)
        self.SetSelection(-1,-1)    # select all text

        
    def OnSetFocus(self, event):
        ''' Occurs when the control receives the keyboard focus.
        '''
        if self.debug:
            print "OnSetFocus received by %s" % self.GetName()
        
        self._oldVal = self.Value
        
        if self.SelectOnEntry:
            self.selectAll()
        event.Skip()
    
        
    def OnKillFocus(self, event):
        ''' Occurs when the control loses the keyboard focus.
        '''
        if self.debug:
            print "OnKillFocus received by %s" % self.GetName()
            
        if self.SelectOnEntry:
            try:
                self.SetSelection(0,0)     # select no text in text box
            except AttributeError:
                pass                       # Only text controls have SetSelection()
        self.flushValue()          
        event.Skip()
    
    
    def flushValue(self):
        ''' Save any changes to the underlying bizobj field.
        '''
        curVal = self.Value
            
        if curVal != self._oldVal and self.DataSource and self.DataField:
            response = self.setFieldVal(curVal)
            if not response:
                raise ValueError, "bizobj.setFieldVal() failed."

    
    # Property get/set/del methods follow. Scroll to bottom to see the property
    # definitions themselves.
    def _getSelectOnEntry(self):
        try:
            return self._SelectOnEntry
        except AttributeError:
            return False
    def _setSelectOnEntry(self, value):
        self._SelectOnEntry = bool(value)
        
    def _getDataSource(self):
        try:
            return self._DataSource
        except AttributeError:
            return ''
    def _setDataSource(self, value):
        self._DataSource = str(value)
        
    def _getDataField(self):
        try:
            return self._DataField
        except AttributeError:
            return ''
    def _setDataField(self, value):
        self._DataField = str(value)

    def _getValue(self):
        return self.GetValue()
    def _setValue(self, value):
        self.SetValue(value)
    
    # Property definitions:
    SelectOnEntry = property(_getSelectOnEntry, _setSelectOnEntry, None, 
                        'Specifies whether all text gets selected upon receiving focus. (bool)')
    DataSource = property(_getDataSource, _setDataSource, None,
                        'Specifies the dataset to use as the source of data. (str)')
    DataField = property(_getDataField, _setDataField, None,
                         'Specifies the data field of the dataset to use as the source of data. (str)')
    Value = property(_getValue, _setValue, None,
                        'Specifies the current state of the control (the value of the field). (varies)')
