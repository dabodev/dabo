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
            
            left = self.app.getAppInfo("%s.left" % name)
            top = self.app.getAppInfo("%s.top" % name)
            width = self.app.getAppInfo("%s.width" % name)
            height = self.app.getAppInfo("%s.height" % name)

            if (type(left), type(top)) == (type(int()), type(int())):
                self.SetPosition((left,top))
            if (type(width), type(height)) == (type(int()), type(int())):
                self.SetSize((width,height))
        
    def saveSizeAndPosition(self):
        if self.dApp:
            name = self.GetName()
            
            pos = self.GetPosition()
            size = self.GetSize()
            
            self.app.setAppInfo("%s.left" % name, "I", pos[0])
            self.app.setAppInfo("%s.top" % name, "I", pos[1])
            self.app.setAppInfo("%s.width" % name, "I", size[0])
            self.app.setAppInfo("%s.height" % name, "I", size[1])
        
