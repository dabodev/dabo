''' test.py

    A simple reusable unit testing framework, used by the 
    base class files when run as scripts instead of imported
    as modules. 
'''
    
import wx
from dForm import dForm
from dLabel import dLabel
from dTextBox import dTextBox
from dControlMixin import dControlMixin
from dCommandButton import dCommandButton
from dSpinner import dSpinner
from dEditBox import dEditBox

class Test(object):

    def __init__(self):
        self.app = wx.PySimpleApp()

    def runTest(self, classRef):
        frame = dForm()
        frame.SetSize((300,1))
        object = classRef(frame)
        print "Running test for %s" % (object.GetName())
        object.SetFocus()
        dControlMixin.EVT_FIELDCHANGED(object, object.GetId(), self.OnFieldChanged)
        frame.Show(1)
        self.app.MainLoop()
    
    def testAll(self):
        ''' Create a dForm and populate it with example dWidgets. '''
        frame = dForm()
        frame.SetSize((640,480))
        panel = wx.Panel(frame, -1)
        
        labelWidth = 150
        labelAlignment = wx.ALIGN_RIGHT
        
        vs = wx.BoxSizer(wx.VERTICAL)

        for obj in ((dTextBox(panel), "txt1"), 
                    (dTextBox(panel), "txt2"),
                    (dEditBox(panel), "edt1"),
                    (dSpinner(panel), "spn1"),
                    (dCommandButton(panel), "cmd1")):
            bs = wx.BoxSizer(wx.HORIZONTAL)
            label = dLabel(panel, windowStyle = labelAlignment|wx.ST_NO_AUTORESIZE,
                                    size = (labelWidth, -1))
            label.SetName("lbl%s" % obj[1])
            label.SetLabel("%s:" % obj[1])
            bs.Add(label)
                            
            object = obj[0]
            if isinstance(object, dEditBox):
                expandFlags = wx.EXPAND
            else:
                expandFlags = 0

            object.SetName("%s" % obj[1])
            object.debug = True # shows the events
            bs.Add(object, 1, expandFlags | wx.ALL, 0)

            if isinstance(object, dEditBox):
                vs.Add(bs, 1, wx.EXPAND)
            else:
                vs.Add(bs, 0, wx.EXPAND)
            
            # Set up the frame to receive the notification that the field value changed
            dControlMixin.EVT_FIELDCHANGED(object, object.GetId(), frame.onFieldChanged)
        
        panel.SetSizer(vs)        
        panel.GetSizer().Layout()

        frame.Show(1)
        self.app.MainLoop()

    def OnFieldChanged(self, evt):
        print "onFieldChanged"

if __name__ == "__main__":
    t = Test()
    t.testAll() 
    
