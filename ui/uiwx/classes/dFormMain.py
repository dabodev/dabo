''' dFormMain.py '''
import wx
import dFormMixin as fm

# Different platforms expect different frame types. Notably,
# most users on Windows expect and prefer the MDI parent/child
# type frames.
if wx.Platform == '__WXMSW__':      # Microsoft Windows
    wxFrameClass = wx.MDIParentFrame
    wxPreFrameClass = wx.PreMDIParentFrame
else:
    wxFrameClass = wx.Frame
    wxPreFrameClass = wx.PreFrame

class dFormMain(wxFrameClass, fm.dFormMixin):
    def __init__(self, dApp=None):
    
        self._baseClass = dFormMain
        
        pre = wxPreFrameClass()
        self.beforeInit(pre)                  # defined in dPemMixin
        pre.Create(None, -1, "dFormMain")
        
        self.this = pre.this
        self._setOORInfo(self)
        
        self.SetName("dFormMain")
        self.SetSize((640,480))
        self.SetPosition((0,0))

        fm.dFormMixin.__init__(self, dApp)
        
        if wx.Platform != '__WXMAC__':
            self.CreateStatusBar()
      
        if self.dApp:
            self.setStatusText("Welcome to %s" % self.dApp.getAppInfo("appName"))
            self.SetLabel("%s Version %s" % (self.dApp.getAppInfo("appName"),
                                             self.dApp.getAppInfo("appVersion")))
        else:
            self.SetLabel("Dabo")
            self.setStatusText("Welcome to Dabo!")
        
        self.afterInit()                      # defined in dPemMixin
        
    
if __name__ == "__main__":
    import test
    test.Test().runTest(dFormMain)
