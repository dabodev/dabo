''' test.py

    A simple reusable unit testing framework, used by the 
    base class files when run as scripts instead of imported
    as modules. 
'''
    
import wx
from dForm import dForm
from dControlMixin import dControlMixin

class Test(object):
    def runTest(self, classRef):
        
        # instantiate a simple app object:
        app = wx.PySimpleApp()
        frame = dForm()
        frame.SetSize((300,1))
        object = classRef(frame)
        print "Running test for %s" % (object.GetName())
        object.SetFocus()
        dControlMixin.EVT_FIELDCHANGED(object, object.GetId(), self.OnFieldChanged)
        frame.Show(1)
        app.MainLoop()
        
    def OnFieldChanged(self, evt):
        print "onFieldChanged"

if __name__ == "__main__":
    print "Testing using textBox..."
    from dTextBox import dTextBox
    Test().runTest(dTextBox)
    
