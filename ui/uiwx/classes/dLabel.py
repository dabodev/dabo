import wx
import dControlMixin as cm

class dLabel(wx.StaticText, cm.dControlMixin):
    def __init__(self, parent, name="dLabel", label="", windowStyle=None):
        
        self._baseClass = dLabel
        
        pre = wx.PreStaticText()
        self.beforeInit(pre)                  # defined in dPemMixin
        windowStyle = windowStyle | wx.ST_NO_AUTORESIZE
        pre.Create(parent, -1, label, (-1,-1), (-1,-1), windowStyle)
        
        self.this = pre.this
        self._setOORInfo(self)
        
        cm.dControlMixin.__init__(self, name)
        self.afterInit()                      # defined in dPemMixin
    
        
    def initEvents(self):
        # init the common events:
        cm.dControlMixin.initEvents(self)
        
        # init the widget's specialized event(s):

    # property get/set functions
    def _getAlignment(self):
        if self.hasWindowStyleFlag(wx.ALIGN_RIGHT):
            return 2
        elif self.hasWindowStyleFlag(wx.ALIGN_CENTRE):
            return 1
        else:
            return 0
    def _setAlignment(self, value):
        if value == 0:
            self.addWindowStyleFlag(wx.ALIGN_LEFT)
        elif value == 1:
            self.addWindowStyleFlag(wx.ALIGN_CENTRE)
        elif value == 2:
            self.addWindowStyleFlag(wx.ALIGN_RIGHT)
    
    # property definitions follow:
    Alignment = property(_getAlignment, _setAlignment, None,
                        'Specifies the alignment of the text. (int) \n'
                        '   0 : Left (default) \n'
                        '   1 : Center \n'
                        '   2 : Right')
        
if __name__ == "__main__":
    import test
    test.Test().runTest(dLabel)
