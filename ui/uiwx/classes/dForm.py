import wx
from dControlMixin import dControlMixin

class dForm(wx.Frame, dControlMixin):
    def __init__(self, frame=None):
        wx.Frame.__init__(self, frame, -1, "")
        self.SetName("dForm")
        dControlMixin.__init__(self)
    
    def initEvents(self):
        # init the common events:
        dControlMixin.initEvents(self)

    def onFieldChanged(self, event):
        ''' A control is saying that its value has changed, so action is needed 
            to notify the bizobj.
        '''
        control = self.FindWindowById(event.GetId())
        print "Event onFieldChanged received by %s. Control is %s with new value of %s" % (self.GetName(), 
                           control.GetName(), control.GetValue())

if __name__ == "__main__":
    import test
    test.Test().runTest(dForm)
