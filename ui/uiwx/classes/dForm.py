import wx, dEvents, dControlMixin

class dForm(wx.Frame):
    def __init__(self, frame=None):
        wx.Frame.__init__(self, frame, -1, "")
        self.SetName("dForm")
        self.SetLabel("dForm")
        self.debug = False
        self._bizobjs = []
        self._primaryBizobj = None
        self._dControls = []
    
    def EVT_VALUEREFRESH(win, id, func):
        win.Connect(id, -1, dEvents.EVT_VALUEREFRESH, func)
    
    def addControl(self, control):
        ''' Add the passed dControl reference to this form.
        
            This happens pretty much behind the scenes, from
            dControlMixin.__init__().
        '''
        self._dControls.append(control)
        print "added control %s" % control.GetName()
        
        # Set up the frame to receive the notification that 
        # the field value changed, and the object to receive
        # the notification from the form that it's time to 
        # refresh its value.
        dControlMixin.dControlMixin.EVT_FIELDCHANGED(control, 
                        control.GetId(), self.onFieldChanged)
        dForm.EVT_VALUEREFRESH(self, self.GetId(), control.onValueRefresh)
        
    def onFieldChanged(self, event):
        ''' A control is saying that its value has changed, so action is needed 
            to notify the bizobj.
        '''
        control = self.FindWindowById(event.GetId())
        
        if self.debug:
            print "\nEvent onFieldChanged received by %s.\n"\
                "     Control: %s \n" \
                "  dataSource: %s \n" \
                "   dataField: %s \n" \
                "       Value: %s \n" % (self.GetName(), 
                                    control.GetName(), 
                                    control.dataSource,
                                    control.dataField,
                                    control.GetValue())
       
    def refreshControls(self):
        ''' Raise EVT_VALUEREFRESH which will be caught by all
            registered controls. 
        '''
        evt = dEvents.dEvent(dEvents.EVT_VALUEREFRESH, self.GetId())
        self.GetEventHandler().ProcessEvent(evt)

    def first(self):
        print "in dForm.first(): pretending that success returned from bizobj:"
        self.refreshControls()
    
    def last(self):
        print "in dForm.last(): pretending that success returned from bizobj:"
        self.refreshControls()
        
    def prior(self):
        print "in dForm.prior(): pretending that success returned from bizobj:"
        self.refreshControls()
        
    def next(self):
        print "in dForm.next(): pretending that success returned from bizobj:"
        self.refreshControls()
    
if __name__ == "__main__":
    import test
    test.Test().runTest(dForm)
