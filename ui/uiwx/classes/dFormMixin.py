''' dFormMixin.py '''
import wx
import dPemMixin as pm
import dMainMenuBar as mnb
import dMenu, dMessageBox

class dFormMixin(pm.dPemMixin):
    def __init__(self, dApp):
        self.dApp = dApp
        
        wx.EVT_CLOSE(self, self.OnClose)
        wx.EVT_SET_FOCUS(self, self.OnSetFocus)
        wx.EVT_KILL_FOCUS(self, self.OnKillFocus)
        wx.EVT_ACTIVATE(self, self.OnActivate)
        
        if self.Parent == wx.GetApp().GetTopWindow():
            self.dApp.uiForms.add(self)
        
        self.restoredSP = False
        
        if self.dApp:
            self.SetMenuBar(mnb.dMainMenuBar(self))
            self.afterSetMenuBar()

        
    def OnActivate(self, event): 
        if bool(event.GetActive()) == True and self.restoredSP == False:
            # Restore the saved size and position, which can't happen 
            # in __init__ because we may not have our name yet.
            self.restoredSP = True
            if wx.GetApp().GetTopWindow() == self and wx.Platform == '__WXMAC__':
                self.SetSize((1,1))
            else:
                self.restoreSizeAndPosition()
        event.Skip()
    
    
    def afterSetMenuBar(self):
        ''' Subclasses can extend the menu bar here.
        '''
        pass
        
                    
    def getMenu(self):
        ''' Get the navigation menu for this form.
        
        Every form maintains an internal menu of actions appropriate to itself.
        For instance, a dForm with a primary bizobj will maintain a menu with 
        'requery', 'save', 'next', etc. choices. 
            
        This function sets up the internal menu, which can optionally be 
        inserted into the mainForm's menu bar during SetFocus.
        '''
        menu = dMenu.dMenu()
        return menu
    
        
    def OnClose(self, event):
        if self.GetParent() == wx.GetApp().GetTopWindow():
            self.dApp.uiForms.remove(self)
        self.saveSizeAndPosition()
        event.Skip()

        
    def OnSetFocus(self, event):
        event.Skip()

        
    def OnKillFocus(self, event):
        event.Skip()
    
        
    def restoreSizeAndPosition(self):
        ''' Restore the saved window geometry for this form.
        
        Ask dApp for the last saved setting of height, width, left, and top, 
        and set those properties on this form.
        '''
        if self.dApp:
            name = self.GetName()
            
            left = self.dApp.getUserSetting("%s.left" % name)
            top = self.dApp.getUserSetting("%s.top" % name)
            width = self.dApp.getUserSetting("%s.width" % name)
            height = self.dApp.getUserSetting("%s.height" % name)

            if (type(left), type(top)) == (type(int()), type(int())):
                self.SetPosition((left,top))
            if (type(width), type(height)) == (type(int()), type(int())):
                self.SetSize((width,height))
        
                
    def saveSizeAndPosition(self):
        ''' Save the current size and position of this form.
        '''
        if self.dApp:
            if self == wx.GetApp().GetTopWindow():
                for form in self.dApp.uiForms:
                    try:
                        form.saveSizeAndPosition()
                    except wx.PyDeadObjectError:
                        pass
            
            name = self.GetName()
            
            pos = self.GetPosition()
            size = self.GetSize()
            
            self.dApp.setUserSetting("%s.left" % name, "I", pos[0])
            self.dApp.setUserSetting("%s.top" % name, "I", pos[1])
            self.dApp.setUserSetting("%s.width" % name, "I", size[0])
            self.dApp.setUserSetting("%s.height" % name, "I", size[1])
        
            
    def setStatusText(self, *args):
        ''' Set the text of the status bar.

        Call this instead of SetStatusText() and dabo will decide whether to 
        send the text to the main frame or this frame. This matters with MDI
        versus non-MDI forms.
        '''
        if isinstance(self, wx.MDIChildFrame):
            controllingFrame = self.dApp.mainFrame
        else:
            controllingFrame = self
        if controllingFrame.GetStatusBar():
            controllingFrame.SetStatusText(*args)
            controllingFrame.GetStatusBar().Update()

        
    def _appendToMenu(self, menu, caption, function, bitmap=wx.NullBitmap):
        menuId = wx.NewId()
        item = wx.MenuItem(menu, menuId, caption)
        item.SetBitmap(bitmap)
        menu.AppendItem(item)
        
        if isinstance(self, wx.MDIChildFrame):
            controllingFrame = self.dApp.mainFrame
        else:
            controllingFrame = self
        wx.EVT_MENU(controllingFrame, menuId, function)

        
    def _appendToToolBar(self, toolBar, caption, bitmap, function, statusText=""):
        toolId = wx.NewId()
        toolBar.AddSimpleTool(toolId, bitmap, caption, statusText)
        
        if isinstance(self, wx.MDIChildFrame):
            controllingFrame = self.dApp.mainFrame
        else:
            controllingFrame = self
        wx.EVT_MENU(controllingFrame, toolId, function)
    

    # property get/set/del functions follow:
    def _getIcon(self):
        return self._Icon
    def _setIcon(self, icon):
        self.SetIcon(icon)
        self._Icon = icon       # wx doesn't provide GetIcon()
        
    def _getIconBundle(self):
        return self._Icons
    def _setIconBundle(self, icons):
        self.SetIcons(icons)
        self._Icons = icons       # wx doesn't provide GetIcons()
        
    
    
    # property definitions follow:
    Icon = property(_getIcon, _setIcon, None, 'Specifies the icon for the form. (wxIcon)')
    IconBundle = property(_getIconBundle, _setIconBundle, None,
                            'Specifies the set of icons for the form. (wxIconBundle)')
