''' daboApp.py: The application object and the main frame object. '''

import dynamicViewWidgets as dynview
import sys, os, wx, wx.help, mainMenu
import dabo.db

class MainFrame(wx.MDIParentFrame):
    def __init__(self, parent, ID, title, app):
        wx.MDIParentFrame.__init__(self, parent, ID, title,
        wx.DefaultPosition, wx.Size(640, 480))

        self.app = app
        self.CreateStatusBar()
        self.SetStatusText("Welcome to %s" % self.app.getAppInfo("appName"))
        
        self.SetMenuBar(mainMenu.MainMenuBar(self))
        self.restoreSizeAndPosition()
        
        wx.EVT_CLOSE(self, self.OnClose)

    def restoreSizeAndPosition(self):
        left = self.app.getAppInfo("mainFrame.left")
        top = self.app.getAppInfo("mainFrame.top")
        width = self.app.getAppInfo("mainFrame.width")
        height = self.app.getAppInfo("mainFrame.height")
        
        if (type(left), type(top)) == (type(int()), type(int())):
            self.SetPosition((left,top))
        if (type(width), type(height)) == (type(int()), type(int())):
            self.SetSize((width,height))
        
    def saveSizeAndPosition(self):
        pos = self.GetPosition()
        size = self.GetSize()
        self.app.setAppInfo("mainFrame.left", "I", pos[0])
        self.app.setAppInfo("mainFrame.top", "I", pos[1])
        self.app.setAppInfo("mainFrame.width", "I", size[0])
        self.app.setAppInfo("mainFrame.height", "I", size[1])
        
    
    def OnFileOpen(self, event):
        menuId = event.GetId()
        dynamicViewName = self.app.getDynamicViewNameFromId(menuId)      
        if dynamicViewName <> None:
            frame = dynview.DynamicViewFrame(self, dynamicViewName, 
                self.app.dynamicViews, False)
            frame.Show(True)
        else:
            print "FIXME: MenuItem doesn't have a dynamicViewName set...."
    
    def OnAbout(self, event):
        pass 
        #dlg = aboutWindow.AboutOpenFox(self)
        #dlg.ShowModal()
        #dlg.Destroy()

    def getTopDynamicNotebook(self):
        ''' return the active dynamic notebook, or None '''
        
        # If focus is not on any control, this proc won't find
        # any dynamic notebook...
        
        object = wx.GetActiveWindow()
        
        if object <> None:
                while object.GetParent() <> None:
                    #print object.GetName(), object.GetTitle()
                    if object.GetClassName() == "wxNotebook":
                        break
                    object = object.GetParent()
        
        if object.GetClassName() == "wxNotebook":
            return object
        else:
            return None
        
    def dynamicFramePageChange(self, pageNumber):
        ''' Pages can't have keyboard accelerators like in VFP: argh. And I can't
            figure out the best way to fake it. Until I have a good solution, I at
            least want it to work, so I've made menu entries that have Alt+1, Alt+2
            keyboard accelerators, and those need to correspond to page1, page2, etc.
            of the dynamicviewframe's notebook. '''
        object = self.getTopDynamicNotebook()
        if object <> None:
            if object.GetPageCount() > pageNumber:
                object.SetSelection(pageNumber)
            
        
    def OnNewRecord(self, event):
        notebook = self.getTopDynamicNotebook()
        if notebook <> None:
            # Find the right wicket (childView, dynamicFrame) and then
            # call it's newRecord() method.
            try:
                wicket = notebook.GetPage(notebook.GetSelection()).wicket
            except AttributeError:
                wicket = notebook.frame.wicket
            wicket.newRecord()
        event.Skip()
        
    def OnAlt1(self, event):
        self.dynamicFramePageChange(0)
        event.Skip()
        
    def OnAlt2(self, event):
        self.dynamicFramePageChange(1)
        event.Skip()
        
    def OnAlt3(self, event):
        self.dynamicFramePageChange(2)
        event.Skip()
    
    def OnAlt4(self, event):
        self.dynamicFramePageChange(3)
        event.Skip()
    
    def OnClose(self, event):
        self.saveSizeAndPosition()
        event.Skip()
            
    def OnExit(self, event):
        self.Close(True)

    def statusMessage(self, message=""):
        statusBar = self.GetStatusBar()
        try:
            statusBar.PopStatusText()
        except:
            pass
        statusBar.PushStatusText(message)
        statusBar.Update()  # Refresh() doesn't work, and this is only needed sometimes.
        
class uiApp(wx.App):
    def OnInit(self):
        return True

    def setup(self, dApp):
        wx.InitAllImageHandlers()
        self.helpProvider = wx.help.SimpleHelpProvider()
        wx.help.HelpProvider_Set(self.helpProvider)

        self.dApp = dApp
        
        self.mainFrame = MainFrame(None, -1, 
                   "%s Version %s" % (self.getAppInfo("appName"), self.getAppInfo("appVersion")),
                   self)
        self.mainFrame.Show(True)
        self.SetTopWindow(self.mainFrame)
    
    def start(self, dApp):
        self.setup(dApp)
        self.MainLoop()
    
    def areYouSure(self, message="Are you sure?", defaultNo=False, style=0):
        style = style|wx.YES_NO|wx.ICON_QUESTION
        if defaultNo:
            style = style|wx.NO_DEFAULT
            
        dlg = wx.MessageDialog(self.GetTopWindow(), 
                                message, 
                                self.getAppInfo("appName"),
                                style)    
        retval = dlg.ShowModal()
        dlg.Destroy()
        
        if retval in (wx.ID_YES, wx.ID_OK):
            return True
        else:
            return False
            
        
    def getAppInfo(self, item, user="*", system="*"):
        ''' Return the value of the dabosettings table that corresponds to the 
            item, user, and system id passed. Based on the ctype field in the 
            dabosettings table, convert the return value into the appropriate
            type first.

            Types:    I: Int
                      N: Float
                      C: String
                      M: String
                      D: Date, saved as a string 3-tuple of integers '(year,month,day)'
                      T: DateTime, saved as a string 9-tuple of integers '(year,month,day,hour,minute,second,?,?,?)'

	'''
        
        sql = (' select cvaluetype as cvaluetype, '
               '        mvalue as mvalue '
               '   from dabosettings '
               '  where mname = "%s" '
               '    and cuserid = "%s" '
               '    and csystemid = "%s" '
               '    and ldeleted=0' % ( item, user, system))
 
        try:
            rs = self.dbc.dbRecordSet(sql)
            try:
                type = rs[0].cvaluetype
                val = rs[0].mvalue
            except IndexError:
                type = None
                val = None

            if type in ('C', 'M'):
                return str(val)
            elif type in ('I',):
                return int(val)
            elif type in ('N',):
                return float(val)
            elif type in ('D','T'):
                timeTuple = eval(val)
                if type(timeTuple) == type(tuple()):
                    return val
                else:
                    return None
            else:
                return None
        except:
            return None
            
    def setAppInfo(self, item, valueType, value, user="*", system="*"):
        ''' Set the value of the dabosettings table that corresponds to the
            item, user, and systemid passed. If it doesn't exist in the table,
            add it. See self.getAppInfo() for the type codes. '''

        import time

        # convert value to string type for saving to db:
        value = str(value)
            
        # determine if the entry already exists in the dabosettings table:
        sql = (' select count(*) as ncount from dabosettings '
               '  where mname = "%s" '
               '    and cuserid = "%s" '
               '    and csystemid = "%s" '
               '    and ldeleted = 0 ' % ( item, user, system))

        try:
            rs = self.dbc.dbRecordSet(sql)
            if rs[0].ncount > 0:
                # update the existing record
                sql = (' update dabosettings '
                    '    set cvaluetype = "%s", '
                    '        mvalue = "%s" '
                    '  where mname = "%s" '
                    '    and cuserid = "%s" '
                    '    and csystemid = "%s" '
                    '    and ldeleted = 0 ' % (valueType,value,item,user,system))     
            else:
                # insert a new record
                sql = (' insert into dabosettings (cvaluetype, '
                    '                           mvalue, '
                    '                           mname, '
                    '                           cuserid, '
                    '                           csystemid) '
                    '   values ("%s","%s","%s","%s","%s") '
                            % (valueType,value,item,user,system))     

            self.dbc.dbCommand(sql)
        except:
            pass
