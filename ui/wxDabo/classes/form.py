import wx
import common

class Form(wx.Frame, common.Common):
    def __init__(self, frame=None):
        wx.Frame.__init__(self, frame, -1, "")
        self.SetName("Form")
        common.Common.__init__(self)
    
    def initEvents(self):
        # init the common events:
        common.Common.initEvents(self)

if __name__ == "__main__":
    import test
    test.Test().runTest(Form)