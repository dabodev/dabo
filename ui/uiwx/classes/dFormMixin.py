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
            
            left = self.dApp.getAppInfo("%s.left" % name)
            top = self.dApp.getAppInfo("%s.top" % name)
            width = self.dApp.getAppInfo("%s.width" % name)
            height = self.dApp.getAppInfo("%s.height" % name)

            if (type(left), type(top)) == (type(int()), type(int())):
                self.SetPosition((left,top))
            if (type(width), type(height)) == (type(int()), type(int())):
                self.SetSize((width,height))
        
    def saveSizeAndPosition(self):
        if self.dApp:
            name = self.GetName()
            
            pos = self.GetPosition()
            size = self.GetSize()
            
            self.dApp.setAppInfo("%s.left" % name, "I", pos[0])
            self.dApp.setAppInfo("%s.top" % name, "I", pos[1])
            self.dApp.setAppInfo("%s.width" % name, "I", size[0])
            self.dApp.setAppInfo("%s.height" % name, "I", size[1])
        
