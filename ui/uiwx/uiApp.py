''' daboApp.py: The application object and the main frame object. '''

import dynamicViewWidgets as dynview
import sys, os, wx, wx.help, mainMenu
import dabo.db

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
