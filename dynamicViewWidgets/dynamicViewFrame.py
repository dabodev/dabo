import wx, dynamicViewGrid, dynamicViewNotebook
import dynamicViewBase as dynview
import wicket

class DynamicViewFrame(wx.MDIChildFrame):
    def __init__(self, parent, viewName, dynamicViews, forceShowAllColumns=False):
        try:
            frameCaption = dynamicViews[viewName]["caption"]
        except KeyError:
            frameCaption = viewName

        wx.MDIChildFrame.__init__(self, parent, -1, frameCaption)

        self.wicket = wicket.Wicket(self, "dynamicFrame", viewName, dynamicViews, forceShowAllColumns)
        self.createNotebook()
    
    def createNotebook(self):
        self.notebook = dynamicViewNotebook.DynamicViewNotebook(self)
    
