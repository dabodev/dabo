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
    
    def initEvents(self):
        pass
    
    def refresh(self):
        ''' Ask the dForm for the current value of the field.'''
        
        if self.dataSource and self.dataField:
            val = self.dForm.getFieldVal(self.dataSource, self.dataField)
            self.SetValue(val)
        else:
            print "... no connected dataSource or dataField"
    
    def EVT_FIELDCHANGED(win, id, func):
        win.Connect(id, -1, dEvents.EVT_FIELDCHANGED, func)

    def onValueRefresh(self, event): 
        print "onValueRefresh received by %s" % (self.GetName(),)
        self.refresh()
        event.Skip()

    def OnSetFocus(self, event):
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
                self.SetSelection(-1,-1) # select all text
        except:
            pass
            
        event.Skip()
    
    def OnKillFocus(self, event):
        try:
            if self.selectOnEntry == True:
                self.SetSelection(0,0) # selects no text in text box
        except:
            pass
        try:
            curVal = self.GetValue()
        except AttributeError:
            curVal = None
            
        if curVal <> self._oldVal:
            # Raise an event that the field value has changed,
            # in case someone cares.  -- Is this useful for anything?
            evt = dEvents.dEvent(dEvents.EVT_FIELDCHANGED, self.GetId())
            self.GetEventHandler().ProcessEvent(evt)

            # Update the bizobj
            if self.dataSource and self.dataField:
                response = self.dForm.setFieldVal(self.dataSource, 
                                                  self.dataField, curVal)
                if not response:
                    print "bizobj.setFieldVal failed."
            else:
                print "... no connected dataSource or dataField"

        event.Skip()