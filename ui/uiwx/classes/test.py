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
from dCommandButton import *
from dSpinner import dSpinner
from dEditBox import dEditBox
from dVCR import dVCR
from dabo.biz import dBizobj
from dabo.db.dConnection import dConnection

class bizZip(dBizobj):
    dataSource = "zipcodes"
    keyField = "iid"
    sql = "select * from zipcodes where ccity like 'san f%' "
    defaultValues = {"ccity":"Penfield", "cStateProv":"NY", "czip":"14526"}

def getConnInfo():
    from dabo.db.dConnectInfo import dConnectInfo
    ci = dConnectInfo('MySQL')
    ci.host = 'leafe.com'
    ci.dbName = "webtest"
    ci.user = 'test'
    ci.password = 'test3'
    return ci

def openConn():
    return dConnection(getConnInfo())
    
def getBiz():
    biz = bizZip(openConn())
    return biz

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
        frame.debug = True
        frame.SetLabel("A test of all the dControls")
        
        biz = getBiz()
        frame.addBizobj(biz)
        
        panel = wx.Panel(frame, -1)
        
        labelWidth = 150
        labelAlignment = wx.ALIGN_RIGHT
        
        vs = wx.BoxSizer(wx.VERTICAL)

        for obj in ((dTextBox(panel), "txtCounty", "ccounty"), 
                    (dTextBox(panel), "txtCity", "ccity"),
                    (dTextBox(panel), "txtZipcode", "czip"),
                    (dEditBox(panel), "edt1"),
                    (dEditBox(panel), "edt2"),
                    (dSpinner(panel), "spn1", "iid"),
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
            
            object.dataSource = biz.dataSource
            if len(obj) > 2:
                # set the dataField:
                object.dataField = obj[2]
                object.refresh()
                
            bs.Add(object, 1, expandFlags | wx.ALL, 0)

            if isinstance(object, dEditBox):
                vs.Add(bs, 1, wx.EXPAND)
            else:
                vs.Add(bs, 0, wx.EXPAND)

        bs = wx.BoxSizer(wx.HORIZONTAL)
        vcr = dVCR(panel)
        bs.Add(vcr, 1, wx.ALL, 0)
        
        button = dCommandButtonSave(panel)
        bs.Add(button, 1, wx.ALL, 0)
        
        button = dCommandButtonCancel(panel)
        bs.Add(button, 1, wx.ALL, 0)

        vs.Add(bs, 0, wx.EXPAND)
                    
        panel.SetSizer(vs)        
        panel.GetSizer().Layout()

        frame.Show(1)
        self.app.MainLoop()

    def OnFieldChanged(self, evt):
        print "onFieldChanged"

if __name__ == "__main__":
    t = Test()
    t.testAll() 
    
