import wx
from dPage import *
from dControlMixin import dControlMixin
import dIcons

class dPageFrame(wx.Notebook, dControlMixin):
    def __init__(self, parent, name="dPageFrame"):
        wx.Notebook.__init__(self, parent, -1)
        dControlMixin.__init__(self, name)
        self.lastSelection = 0
        self.addDefaultPages()        

        
    def initEvents(self):
        dControlMixin.initEvents(self)
        wx.EVT_NOTEBOOK_PAGE_CHANGED(self, self.GetId(), self.OnPageChanged)

        
    def addDefaultPages(self):
        ''' Add the standard pages to the pageframe.
        
        Subclasses may override or extend.
        '''
        il = wx.ImageList(16,16)
        il.Add(dIcons.getIconBitmap("checkMark"))
        il.Add(dIcons.getIconBitmap("browse"))
        il.Add(dIcons.getIconBitmap("edit"))
        
        self.AssignImageList(il)
        self.AddPage(dSelectPage(self), "Select", imageId=0)
        self.AddPage(dBrowsePage(self), "Browse", imageId=1)
        self.AddPage(dEditPage(self), "Edit", imageId=2)
        
        
    def OnPageChanged(self, event):
        ls = self.lastSelection
        cs = event.GetSelection()

        event.Skip()    # This must happen before onLeave/EnterPage below

        newPage = self.GetPage(cs)
        oldPage = self.GetPage(ls)    
        
        oldPage.onLeavePage()
        newPage.onEnterPage()
        
        self.lastSelection = cs
