''' dControlMixin.py: Provide behavior common to all dControls '''

import wx, dEvents

class dControlMixin:
    ''' mixin class: inherited by the dabo widgets to
        provide common functionality. '''
    
    def __init__(self, name):
        self.debug = False
        self.SetName(name)
        # Default label and (if control can handle a text value), value
        self.SetLabel(self.getDefaultText())
        
        # Subclass will intercept the initEvents first, allowing
        # the framework user to completely override if desired.    
        self.initEvents()
        
        self.focusSet = False
        
        self.dForm = self.getDform()
        self.addToDform()
    
    def getDform(self):
        ''' Crawl up the containership tree to find the dForm, if any. '''
        import dForm
        obj = self
        frm = None
        while obj:
            parent = obj.GetParent()
            if isinstance(parent, dForm.dForm):
                frm = parent
                break
            else:
                obj = parent
        return frm
    
    def addToDform(self):
        if self.dForm:
            self.dForm.addControl(self)
                
    def getDefaultText(self):
        return "Dabo: %s" % self.GetName()
        
    def initEvents(self):
        ''' initEvents(object)
            All windows share common events, which are initialized here
            instead of separately in each widget. 
        '''
        
        wx.EVT_ENTER_WINDOW(self, self.OnEnterWindow) 
        wx.EVT_LEAVE_WINDOW(self, self.OnLeaveWindow) 
        wx.EVT_SET_FOCUS(self, self.OnSetFocus)
        wx.EVT_KILL_FOCUS(self, self.OnKillFocus)

    
    # Common event callbacks (override in subclasses):
    def OnSetFocus(self, event): event.Skip()
        
    def OnKillFocus(self, event):event.Skip()
            
    def OnEnterWindow(self, event):
        event.Skip()
        
    def OnLeaveWindow(self, event):
        event.Skip()

    def setDefaultFont(self):
        ''' Based on control type, set the default font '''
        font = self.GetFont()
        if self.GetClassName() == "wxStaticText":
            font.SetPointSize(10)
        self.SetFont(font)
   
