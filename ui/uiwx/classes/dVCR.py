''' dVCR.py  : Simple navigation control '''

import wx
from dCommandButton import dCommandButton

class NavButton(dCommandButton):
    def __init__(self, parent):
        dCommandButton.__init__(self, parent)
        self.SetName("navButton")
        self.SetSize((40,-1))
    
    def OnButton(self, event):
        self.navigate()

    def navigate(self, func):
        #print "Applying function %s" % func
        apply(func)
        
class First(NavButton):
    def __init__(self, parent):
        NavButton.__init__(self, parent)
        self.SetName("navFirst")
        self.SetLabel(" << ")
    
    def navigate(self):
        NavButton.navigate(self, self.dForm.first)
    
class Last(NavButton):
    def __init__(self, parent):
        NavButton.__init__(self, parent)
        self.SetName("navLast")
        self.SetLabel(" >> ")
    
    def navigate(self):
        NavButton.navigate(self, self.dForm.last)
    
class Prior(NavButton):
    def __init__(self, parent):
        NavButton.__init__(self, parent)
        self.SetName("navPrior")
        self.SetLabel(" < ")
    
    def navigate(self):
        NavButton.navigate(self, self.dForm.prior)
    
class Next(NavButton):
    def __init__(self, parent):
        NavButton.__init__(self, parent)
        self.SetName("navNext")
        self.SetLabel(" > ")
    
    def navigate(self):
        NavButton.navigate(self, self.dForm.next)

class dVCR(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        
        bs = wx.BoxSizer(wx.HORIZONTAL)
        
        nav = First(self)
        bs.Add(nav, 0, wx.ALL, 0)

        nav = Prior(self)
        bs.Add(nav, 0, wx.ALL, 0)
        
        nav = Next(self)
        bs.Add(nav, 0, wx.ALL, 0)
        
        nav = Last(self)
        bs.Add(nav, 0, wx.ALL, 0)

        self.SetSizer(bs)        
        self.GetSizer().Layout()
                
