import wx, dEvents

class dForm(wx.Frame):
    def __init__(self, frame=None):
        wx.Frame.__init__(self, frame, -1, "")
        self.SetName("dForm")
        self.SetLabel("dForm")
        self.debug = False
        self._bizobjs = []
        self._primaryBizobj = None
    
    def EVT_VALUEREFRESH(win, id, func):
        win.Connect(id, -1, dEvents.EVT_VALUEREFRESH, func)
    
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

        # Pretend the bizobj has gone to the next record. 
        # The controls must be notified to refresh themselves.
        self.refreshControls()
        
    def refreshControls(self):
        ''' Raise EVT_VALUEREFRESH which will be caught by all
            registered controls. 
        '''
        evt = dEvents.dEvent(dEvents.EVT_VALUEREFRESH, self.GetId())
        self.GetEventHandler().ProcessEvent(evt)

if __name__ == "__main__":
    import test
    test.Test().runTest(dForm)
