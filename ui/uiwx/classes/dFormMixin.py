''' dFormMixin.py '''
import wx

class dFormMixin:
    def __init__(self, dApp):
        self.dApp = dApp
        self.restoreSizeAndPosition()
        
        wx.EVT_CLOSE(self, self.OnClose)
    
    def OnClose(self, event):
        self.saveSizeAndPosition()
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
        
