''' dVCR.py  : Simple data navigation/action control '''

import wx
from dCommandButton import dCommandButton

class VcrButton(dCommandButton):
    def __init__(self, parent, name, caption, func, size=(-1,-1)):
        dCommandButton.__init__(self, parent)
        self.SetName(name)
        self.SetSize(size)
        self.SetLabel(caption)
        self.func = func
    
    def OnButton(self, event):
        apply(eval("self.dForm.%s" % self.func))

class dVCR(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        
        bsNav = wx.BoxSizer(wx.HORIZONTAL)
        
        but = VcrButton(self, "cmdFirst", "<<", 
                        "first", (40,-1))
        bsNav.Add(but, 0, wx.ALL, 0)
        
        but = VcrButton(self, "cmdPrior", "<", 
                        "prior", (40,-1))
        bsNav.Add(but, 0, wx.ALL, 0)
        
        but = VcrButton(self, "cmdNext", ">", 
                        "next", (40,-1))
        bsNav.Add(but, 0, wx.ALL, 0)

        but = VcrButton(self, "cmdLast", ">>", 
                        "last", (40,-1))
        bsNav.Add(but, 0, wx.ALL, 0)
        
        bsMain = wx.BoxSizer(wx.HORIZONTAL)
        bsMain.Add(bsNav, 0, wx.EXPAND, 0)

        but = VcrButton(self, "cmdRequery", "Requery", 
                        "requery")
        bsMain.Add(but, 0, 0, 0)
        
        but = VcrButton(self, "cmdNew", "New", 
                        "new")
        bsMain.Add(but, 0, 0, 0)
        
        but = VcrButton(self, "cmdDelete", "Delete", 
                        "delete")
        bsMain.Add(but, 0, 0, 0)

        but = VcrButton(self, "cmdDeleteAll", "Delete All", 
                        "deleteAll")
        bsMain.Add(but, 0, 0, 0)
        
        but = VcrButton(self, "cmdSave", "Save", 
                        "save")
        bsMain.Add(but, 0, 0, 0)
        
        but = VcrButton(self, "cmdCancel", "Cancel", 
                        "cancel")
        bsMain.Add(but, 0, 0, 0)

        self.SetSizer(bsMain)        
        self.GetSizer().Layout()
                
