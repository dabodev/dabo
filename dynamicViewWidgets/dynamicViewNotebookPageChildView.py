import wx
import dynamicViewGrid
import dynamicViewBase as dynview
import dabo.classes as classes
import wicket
from dynamicViewNotebookPageBrowse import BrowsePage

class RecordLabel(classes.Label):
    def __init__(self, parent):
        classes.Label.__init__(self, parent)
        font = self.GetFont()
        font.SetWeight(wx.BOLD)
        font.SetPointSize(12)
        self.SetFont(font)
                            
class ChildViewPage(BrowsePage):
    def __init__(self, parent, viewName):
        self.viewName = viewName
        BrowsePage.__init__(self, parent)
        self.SetName("childViewPage")

    def fillItems(self):        
        self.createWicket()
        
        self.recordLabel = RecordLabel(self)
        self.GetSizer().Add(self.recordLabel,0,wx.EXPAND)

        BrowsePage.fillItems(self)
    
    def getViewCaption(self):
        return "%s: %s" % (self.wicket.getCaption(),
                self.recordLabel.GetLabel())
                
    def createWicket(self):
        self.masterWicket = self.notebook.frame.wicket
        self.wicket = wicket.Wicket(self, "childView", self.viewName, 
                        self.masterWicket.dynamicViews, self.masterWicket.forceShowAllColumns)
        self.wicket.setMasterWicket(self.masterWicket)
        self.requery()
        
    def createGrid(self):
        self.destroyGrid()
        self.grid = dynamicViewGrid.DynamicViewGrid(self, self.wicket)
        self.GetSizer().Add(self.grid, 1, wx.EXPAND)
        
        self.wicket.setGridRef(self.grid)

    def requery(self):
        fkFields = self.wicket.getFkFields()
        viewObject = self.wicket.getViewObject()
        
        fromClause = ""
        whereClause = ""
        
        masterTableName = self.masterWicket.getViewDef()["tableName"]
        masterPkName = self.masterWicket.getPkField()
        masterKeyValue = self.masterWicket.getCurrentKeyValue()
        if masterKeyValue == None:
            masterKeyValue = 0
            
        for fkField in fkFields:
            fieldName = fkField["fieldName"]
            foreignFieldName = fkField["foreignFieldName"]
            foreignTableName = foreignFieldName[:foreignFieldName.find(".")]
            fromClause = ''.join((fromClause, "inner join %s on %s=%s" % (foreignTableName,
                                    foreignFieldName, fieldName)))
            #print foreignFieldName, "%s.%s" % (masterTableName, masterPkName)
            if foreignFieldName == "%s.%s" % (masterTableName, masterPkName):
                if len(whereClause) == 0:
                    char = ""
                else:
                    char = " AND "
                whereClause = ''.join((whereClause, char, "%s = %s" % (fieldName, masterKeyValue)))            

        viewObject.fromClause = fromClause
        viewObject.whereClause = whereClause
            
        sql = viewObject.getSQL()
        
        #try:        
        self.wicket.viewCursor = viewObject.viewRequery(sql,wx.GetApp().dbc)
       # except:
        #    self.wicket.viewCursor = None
        
        if self.wicket.viewCursor <> None:
            statusMessage = "%i record%s selected in %s second%s" % (
                    viewObject.lastQueryTally, 
                   (viewObject.lastQueryTally == 1 and ('',) or ('s',))[0], 
                   viewObject.lastQueryTime,
                   (viewObject.lastQueryTime == 1 and ('',) or ('s',))[0])
        else:
            statusMessage = "Error getting dynamic view..."

        try:         
            self.statusLabel.SetLabel(statusMessage)              
        except AttributeError:
            pass # during page creation, this happens

    def onEnterPage(self):
        self.requery()
        self.wicket.fillGrid()
        self.recordLabel.SetLabel(self.notebook.frame.wicket.getCurrentRecordLabel())
        
