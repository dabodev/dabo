''' dDataControlMixin.py: Provide behavior common to all 
    data-aware dControls.
'''

import wx, dEvents, dForm

class dDataControlMixin:
    ''' mixin class: inherited by the dabo widgets to
        provide common functionality. '''
    
    def __init__(self):
        self._oldVal = None
    
        self.selectOnEntry = False
        
        self.dataSource = None
        self.dataField = None
        self.bizobj = None
        
    def initEvents(self):
        pass

    def getFieldVal(self):
        ''' Ask the bizobj what the current value of the field is. '''
        
        if not self.bizobj:
            # Need to ask the form for the bizobj reference
            self.bizobj = self.dForm.getBizobj(self.dataSource)
        return self.bizobj.getFieldVal(self.dataField)
    
        
    def setFieldVal(self, value):
        ''' Ask the bizobj to update the field value. '''
        
        if not self.bizobj:
            # Need to ask the form for the bizobj reference
            self.bizobj = self.dForm.getBizobj(self.dataSource)
        return self.bizobj.setFieldVal(self.dataField, value)
        
        
    def refresh(self):
        ''' Update control value to match the current value from the bizobj. '''
        if self.dataSource and self.dataField:
            try:
                self.SetValue(self.getFieldVal())
            except TypeError:
                print "type error"
        

    def onValueRefresh(self, event): 
        if self.debug:
            print "onValueRefresh received by %s" % (self.GetName(),)
        self.refresh()
        event.Skip()

    
    def OnSetFocus(self, event):
        print "OnSetFocus received by %s" % self.GetName()

        try:
            self.dForm.controlWithFocus = self
        except AttributeError:   # perhaps our containing frame isn't a dForm
            pass
            
        try:
            self._oldVal = self.GetValue()
        except AttributeError:   # labels, for example...
            self._oldVal = None
        
        try:
            if (self.selectOnEntry == True and not self.focusSet 
                and len(self.GetValue()) > 0):
                # Select all text, and get rid of the insertion point.
                # Choices of where to put the insertion point are:
                # end of text, beginning of text, or -1, which 
                # experimentation reveals to take it away completely.
                # However, sometimes the value doesn't display with
                # the -1 trick. So... for now, keep at 0...
                self.SetInsertionPoint(0)
                self.SetSelection(-1,-1)          # select all text
        except:
            pass
        
        ### Question: VFP does an implicit refresh() here, just in case
        ###           the control hasn't been updated with the value of
        ###           the field yet. We could do a self.refresh() here,
        ###           or we can be confident this won't be necessary in
        ###           Dabo. Anyway, if you are reading this and having
        ###           this sort of trouble, just uncomment the following
        ###           line and see if it fixes it:
        #self.refresh()
        
        event.Skip()
    
        
    def OnKillFocus(self, event):
        print "OnKillFocus received by %s" % self.GetName()
        event.Skip()
        try:
            if self.selectOnEntry == True:
                self.SetSelection(0,0) # selects no text in text box
        except:
            pass
        
        self.flushValue()
        event.Skip()
    
    
    def flushValue(self):
        try:
            curVal = self.GetValue()
        except AttributeError:
            curVal = None
            
        if curVal != self._oldVal:
            # Update the bizobj
            if self.dataSource and self.dataField:
                response = self.setFieldVal(curVal)
                if not response:
                    print "bizobj.setFieldVal failed."
