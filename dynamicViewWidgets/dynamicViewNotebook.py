import wx
import dynamicViewNotebookPageSelect as selectPage
import dynamicViewNotebookPageBrowse as browsePage
import dynamicViewNotebookPageEdit as editPage
import dynamicViewNotebookPageChildView as childViewPage


class DynamicViewNotebook(wx.Notebook):
    def __init__(self, parent):
        wx.Notebook.__init__(self, parent, -1, style=wx.NB_BOTTOM)
        self.SetName("DynamicViewNotebook")        
        self.frame = parent

        self.addDefaultPages()        
        self.lastSelection = 0

        wx.EVT_NOTEBOOK_PAGE_CHANGED(self, self.GetId(), self.OnPageChanged)
        
        # Put on Browse page by default:
        self.AdvanceSelection()
    
    def addDefaultPages(self):
        """ Add the standard pages, plus the childview page(s) if any,
            as defined in the master view """
        self.AddPage(selectPage.SelectPage(self), "Select")
        self.AddPage(browsePage.BrowsePage(self), "Browse")
        self.AddPage(editPage.EditPage(self, self.frame.wicket), "Edit")
    
        self.GetPage(1).statusLabel.SetLabel(self.initialStatusMessage)
        
        viewdef = self.frame.wicket.getViewDef()
        
        try:
            childViews = viewdef["childViews"]
        except KeyError:
            childViews = []
        
        for childView in childViews:
            self.AddPage(childViewPage.ChildViewPage(self, childView),
                        self.frame.wicket.dynamicViews[childView]["caption"])
            
    def setInitialStatusMessage(self, message):
        self.initialStatusMessage = message
        
    def OnPageChanged(self, event):
        newPage = self.GetPage(event.GetSelection())
        oldPage = self.GetPage(self.lastSelection)    
        
        oldPage.onLeavePage()
        newPage.onEnterPage()
        
        self.lastSelection = self.GetSelection()

        event.Skip()

