import wx, dIcons
import dPageFrame as pgf
import dPageDataNav as pag

class dPageFrameDataNav(pgf.dPageFrame):
    def __init__(self, parent, name="dPageFrameDataNav"):
        super(dPageFrameDataNav, self).__init__(parent, name)
        self.addDefaultPages()        

        
    def addDefaultPages(self):
        ''' Add the standard pages to the pageframe.
        
        Subclasses may override or extend.
        '''
        il = wx.ImageList(16, 16, initialCount=0)
        il.Add(dIcons.getIconBitmap("checkMark"))
        il.Add(dIcons.getIconBitmap("browse"))
        il.Add(dIcons.getIconBitmap("edit"))
        
        self.AssignImageList(il)
        self.AddPage(pag.dSelectPage(self), "Select", imageId=0)
        self.AddPage(pag.dBrowsePage(self), "Browse", imageId=1)
        self.AddPage(pag.dEditPage(self), "Edit", imageId=2)
        
        self.GetPage(0).onEnterPage()
        
