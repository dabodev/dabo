import wx, wx.html
import dynamicViewGrid
import dynamicViewBase as dynview
import dabo.classes as classes
import dynamicViewNotebookPage as page
                    
class BrowsePage(page.Page):
    def __init__(self, parent):
        page.Page.__init__(self, parent, "browsePage")
    
    def fillItems(self):
        self.createGrid()
        
        self.statusLabel = classes.Label(self)
        self.GetSizer().Add(self.statusLabel,0,wx.EXPAND)
        

        buttonbar = wx.BoxSizer(wx.HORIZONTAL)
        
        cmd = classes.CommandButton(self, -1)
        cmd.SetLabel("Preview")
        wx.EVT_BUTTON(cmd, -1, self.onPreview)
        buttonbar.Add(cmd)
        
        cmd = classes.CommandButton(self, -1)
        cmd.SetLabel("Print")
        wx.EVT_BUTTON(cmd, -1, self.onPrint)
        buttonbar.Add(cmd)
        
        self.GetSizer().Add(buttonbar)
        self.GetSizer().Layout()

    def destroyGrid(self):
        try:
            self.GetSizer().Detach(self.grid)
        except AttributeError:
            pass
            
        try:
            self.grid.Destroy()
        except AttributeError:
            pass
            
    def createGrid(self):
        self.destroyGrid()
        self.grid = dynamicViewGrid.DynamicViewGrid(self, self.notebook.frame.wicket)
        self.GetSizer().Add(self.grid, 1, wx.EXPAND)
        
        self.notebook.frame.wicket.setGridRef(self.grid)
        
    def onEnterPage(self):
        self.grid.AutoSizeColumns(True)
        self.grid.SetFocus()
    
    def onPreview(self, event):
        html = self.grid.getHTML(justStub=False)
        win = wx.html.HtmlEasyPrinting("Dabo Quick Print", self.notebook.frame)
        printData = win.GetPrintData()
        setupData = win.GetPageSetupData()
        #printData.SetPaperId(wx.PAPER_LETTER)
        setupData.SetPaperId(wx.PAPER_LETTER)
        if self.grid.GetNumberCols() > 20:
            printData.SetOrientation(wx.LANDSCAPE)
        else:
            printData.SetOrientation(wx.PORTRAIT)
        setupData.SetMarginTopLeft((17,7))
        setupData.SetMarginBottomRight((17,5))
#        setupData.SetOrientation(wx.LANDSCAPE)
        win.SetHeader("<B>%s</B>" % (self.getViewCaption(),))
        win.SetFooter("<CENTER>Page @PAGENUM@ of @PAGESCNT@</CENTER>")
        win.PageSetup()
        win.PreviewText(html)

    def getViewCaption(self):
        return self.notebook.frame.wicket.getCaption()
        
    def onPrint(self, event):
        print "Print"
