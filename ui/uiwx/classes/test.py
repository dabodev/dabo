''' test.py

A simple reusable unit testing framework, used by the base class files when run
as scripts instead of imported as modules. 
    
If you execute, say:
    python dTextBox.py
        
The dTextBox.py's main section will instantiate class Test and do a simple unit 
test of dTextBox.
    
If you instead run this test.py as a script, a form will be instantiated with 
all the dControls.
'''
import wx
from dabo.ui.uiwx import *

class Test(object):
    def __init__(self):
        self.app = wx.PySimpleApp()

    def runTest(self, classRef):
        frame = wx.Frame(None, -1, "")
        frame.SetSize((300,1))
        object = classRef(frame)
        frame.SetLabel("Test of %s" % object.GetName())
        object.SetFocus()
        frame.Show()
        object.Show()
        self.app.MainLoop()
    
    def testAll(self):
        ''' Create a dForm and populate it with example dWidgets. 
        '''
        frame = dForm()
        frame.SetSize((640,480))
        frame.debug = True
        
        frame.SetLabel("Test of all the dControls")
        
        panel = wx.Panel(frame, -1)
        
        labelWidth = 150
        labelAlignment = wx.ALIGN_RIGHT
        
        vs = wx.BoxSizer(wx.VERTICAL)

        for obj in ((dTextBox(panel), "txtCounty", "ccounty"), 
                    (dTextBox(panel), "txtCity", "ccity"),
                    (dTextBox(panel), "txtZipcode", "czip"),
                    (dSpinner(panel), "spn1", "iid"),
                    (dCheckBox(panel), "chk1"),
                    (dEditBox(panel), "edt1")):
            bs = wx.BoxSizer(wx.HORIZONTAL)
            label = dLabel(panel, windowStyle = labelAlignment|wx.ST_NO_AUTORESIZE)
            label.SetSize((labelWidth,-1))
            try:
                lblName = obj[2]
            except IndexError:
                lblName = "%s" % obj[1]
            label.SetName(lblName)
            label.SetLabel("%s:" % lblName)
            bs.Add(label)
                            
            object = obj[0]
            if isinstance(object, dEditBox):
                expandFlags = wx.EXPAND
            else:
                expandFlags = 0

            object.SetName("%s" % obj[1])
            object.debug = True # show the events
            
            bs.Add(object, 1, expandFlags | wx.ALL, 0)

            if isinstance(object, dEditBox):
                vs.Add(bs, 1, wx.EXPAND)
            else:
                vs.Add(bs, 0, wx.EXPAND)

        bs = wx.BoxSizer(wx.HORIZONTAL)
        
        vs.Add(bs, 0, wx.EXPAND)
                    
        panel.SetSizer(vs)        
        panel.GetSizer().Layout()
        
        frame.GetSizer().Add(panel, 1, wx.EXPAND)
        frame.GetSizer().Layout()
        frame.Show(1)
        self.app.MainLoop()

if __name__ == "__main__":
    t = Test()
    t.testAll() 
    
