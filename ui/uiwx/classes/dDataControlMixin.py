''' dDataControlMixin.py: Provide behavior common to all 
    data-aware dControls.
'''

class dDataControlMixin:
    ''' Provide common functionality for the data-aware controls.
    '''
    def __init__(self):
        self._oldVal = None
    
        self.selectOnEntry = False
        
        self.dataSource = None
        self.dataField = None
        self.bizobj = None
        
        
    def initEvents(self):
        pass

        
    def getFieldVal(self):
        ''' Ask the bizobj what the current value of the field is. 
        '''
        if not self.bizobj:
            # Ask the form for the bizobj reference, and cache for next time
            self.bizobj = self.getDform().getBizobj(self.dataSource)
        return self.bizobj.getFieldVal(self.dataField)
    
        
    def setFieldVal(self, value):
        ''' Ask the bizobj to update the field value. 
        '''
        if not self.bizobj:
            # Ask the form for the bizobj reference, and cache for next time
            self.bizobj = self.getDform().getBizobj(self.dataSource)
        return self.bizobj.setFieldVal(self.dataField, value)
        
        
    def refresh(self):
        ''' Update control's value to match the current value from the bizobj.
        '''
        if self.dataSource and self.dataField:
            self.SetValue(self.getFieldVal())
        

    def onValueRefresh(self, event): 
        ''' Occurs when the field value has potentially changed.
        '''
        if self.debug:
            print "onValueRefresh received by %s" % (self.GetName(),)
        self.refresh()
        if self.selectOnEntry and self.getDform().controlWithFocus == self:
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
        
        try:
            self.getDform().controlWithFocus = self
        except AttributeError:   # perhaps the containing frame isn't a dForm
            pass
            
        self._oldVal = self.GetValue()
        
        if self.selectOnEntry:
            self.selectAll()
        event.Skip()
    
        
    def OnKillFocus(self, event):
        ''' Occurs when the control loses the keyboard focus.
        '''
        if self.debug:
            print "OnKillFocus received by %s" % self.GetName()
        try:
            self.SetSelection(0,0)     # select no text in text box
        except AttributeError:
            pass                       # Only text controls have SetSelection()
        self.flushValue()          
        event.Skip()
    
    
    def flushValue(self):
        ''' Save any changes to the underlying bizobj field.
        '''
        curVal = self.GetValue()
            
        if curVal != self._oldVal and self.dataSource and self.dataField:
            response = self.setFieldVal(curVal)
            if not response:
                raise ValueError, "bizobj.setFieldVal() failed."
