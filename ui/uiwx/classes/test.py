''' test.py

    A simple reusable unit testing framework, used by the 
    base class files when run as scripts instead of imported
    as modules. 
'''
    
import wx
from dabo.ui.uiwx import *
from dabo.biz import *
from dabo.db import *

class bizZip(dBizobj):
    dataSource = "zipcodes"
    keyField = "iid"
    sql = "select * from zipcodes where ccity like 'hol%' "
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
        mainFrame = dFormMain()
        #mainFrame.Maximize()
        frame = dForm(mainFrame)
        frame.SetSize((300,1))
        object = classRef(frame)
        print "Running test for %s" % (object.GetName())
        object.SetFocus()
        mainFrame.Show()
        frame.Show()
        object.Show()
        mainFrame.SetSize((640,480))
        self.app.MainLoop()
    
    def testAll(self, withBiz=False):
        ''' Create a dForm and populate it with example dWidgets. '''
        frame = dForm()
        frame.SetSize((640,480))
        frame.debug = True
        
        if withBiz:
            biz = getBiz()
            frame.addBizobj(biz)
            appendCaption = "with bizobj/data test to leafe.com"
        else:
            appendCaption = ""
        frame.SetLabel("A test of all the dControls %s" % appendCaption)
        
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
            
            if withBiz:
                object.dataSource = biz.dataSource
                if len(obj) > 2:
                    object.dataField = obj[2]

            bs.Add(object, 1, expandFlags | wx.ALL, 0)

            if isinstance(object, dEditBox):
                vs.Add(bs, 1, wx.EXPAND)
            else:
                vs.Add(bs, 0, wx.EXPAND)

        bs = wx.BoxSizer(wx.HORIZONTAL)
        
        if withBiz:
            vcr = dVCR(panel)
            bs.Add(vcr, 1, wx.ALL, 0)
        
        vs.Add(bs, 0, wx.EXPAND)
                    
        panel.SetSizer(vs)        
        panel.GetSizer().Layout()

        frame.refreshControls()
        frame.Show(1)
        self.app.MainLoop()

if __name__ == "__main__":
    t = Test()
    t.testAll(withBiz=True) 
    
