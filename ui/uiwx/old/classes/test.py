''' test.py
    A simple reusable unit testing framework, used by the 
    base class files when run as scripts instead of imported
    as modules. '''
    
import wx
import form, common

class Test(object):
    def runTest(self, classRef):
        print "Running test for %s" % (classRef)
        
        # instantiate a simple app object:
        app = wx.PySimpleApp()
        frame = form.Form()
        frame.SetSize((300,1))
        object = classRef(frame)
        object.SetFocus()
        common.EVT_FIELDCHANGED(object, object.GetId(), self.OnFieldChanged)
        frame.Show(1)
        app.MainLoop()
        
    def OnFieldChanged(self, evt):
        print "onFieldChanged"
        
if __name__ == "__main__":
    print "Testing using textBox..."
    import textBox
    Test().runTest(textBox.TextBox)
    
