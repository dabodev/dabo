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

if __name__ == "__main__":
    import test
    test.Test().runTest(dForm)
