''' dFormMixin.py '''
import wx
from dMenu import *

class dFormMixin:
    def __init__(self, dApp):
        self.dApp = dApp
        self.restoreSizeAndPosition()
        self.menuLabel = self.GetLabel()
        
        wx.EVT_CLOSE(self, self.OnClose)
        wx.EVT_SET_FOCUS(self, self.OnSetFocus)
        wx.EVT_KILL_FOCUS(self, self.OnKillFocus)
        
    def getMenu(self):
        ''' dFormMixin.setupMenu(self) -> None
        
            Every form maintains an internal menu of
            actions appropriate to itself. For instance,
            a dForm with a primary bizobj will maintain
            a menu with 'requery', 'save', 'next', etc.
            choices. 
            
            This function sets up the internal menu, which
            can optionally be inserted into the mainForm's
            menu bar during SetFocus.
        '''
        menu = dMenu()
        return menu
    
    def OnClose(self, event):
        self.saveSizeAndPosition()
        if self.dApp and self.GetParent():
            self.dApp.mainFrame.GetMenuBar().removeActiveFormMenu()    
        event.Skip()

    def OnSetFocus(self, event):
        if self.dApp and self.GetParent():
            self.dApp.mainFrame.GetMenuBar().replaceActiveFormMenu(self)
        event.Skip()

    def OnKillFocus(self, event):
        event.Skip()
    
    def restoreSizeAndPosition(self):
        if self.dApp:
            name = self.GetName()
            
            left = self.dApp.getUserSetting("%s.left" % name)
            top = self.dApp.getUserSetting("%s.top" % name)
            width = self.dApp.getUserSetting("%s.width" % name)
            height = self.dApp.getUserSetting("%s.height" % name)

            if (type(left), type(top)) == (type(int()), type(int())):
                self.SetPosition((left,top))
            if (type(width), type(height)) == (type(int()), type(int())):
                self.SetSize((width,height))
        
    def saveSizeAndPosition(self):
        if self.dApp:
            name = self.GetName()
            
            pos = self.GetPosition()
            size = self.GetSize()
            
            self.dApp.setUserSetting("%s.left" % name, "I", pos[0])
            self.dApp.setUserSetting("%s.top" % name, "I", pos[1])
            self.dApp.setUserSetting("%s.width" % name, "I", size[0])
            self.dApp.setUserSetting("%s.height" % name, "I", size[1])
        
