''' dControlMixin.py: Provide behavior common to all controls '''

import wx, dEvents

class dControlMixin:
    ''' mixin class: inherited by the dabo widgets to
        provide common functionality. '''
    
    def __init__(self):
        self.debug = False
        # Default label and (if control can handle a text value), value
        self.SetLabel(self.getDefaultText())
        # Subclass will intercept the initEvents first, allowing
        # the framework user to completely override if desired.    
        self.initEvents()
        self.eventDict = self._getEventDict()
        
        self._oldVal = None
    
        self.selectOnEntry = False
        self.focusSet = False
        
        self.dataSource = None
        self.dataField = None
    
    def EVT_FIELDCHANGED(win, id, func):
        win.Connect(id, -1, dEvents.EVT_FIELDCHANGED, func)

    def getDefaultText(self):
        return "Dabo: %s" % self.GetName()
        
    def initEvents(self):
        ''' initEvents(object)
            All windows share common events, which are initialized here
            instead of separately in each widget. '''
        
        # Every event bound here must have a corresponding callback
        # below, in the "Common event callbacks" section
        wx.EVT_ENTER_WINDOW(self, self.onEvent) 
        wx.EVT_LEAVE_WINDOW(self, self.onEvent) 
        wx.EVT_SET_FOCUS(self, self.onEvent)
        wx.EVT_KILL_FOCUS(self, self.onEvent)


    # Common event callbacks (override in subclasses):
    
    def OnSetFocus(self, event):
        try:
            self._oldVal = self.GetValue()
        except AttributeError:   # labels, for example...
            self._oldVal = None
        
        try:
            if (self.selectOnEntry == True and not self.focusSet 
                and len(self.GetValue()) > 0):
                # Select all text, and get rid of the insertion point.
                # Choices of where to put the insertion point are:
                # end of text, beginning of text, or -1, which 
                # experimentation reveals to take it away completely.
                # However, sometimes the value doesn't display with
                # the -1 trick. So... for now, keep at 0...
                self.SetInsertionPoint(0)
                self.SetSelection(-1,-1) # select all text
        except:
            pass
        
    def OnKillFocus(self, event):
        #print "killfocus: %s" % self.GetValue()
        try:
            if self.selectOnEntry == True:
                self.SetSelection(0,0) # selects no text in text box
        except:
            pass
        try:
            curVal = self.GetValue()
        except AttributeError:
            curVal = None
            
        if curVal <> self._oldVal:
            # Raise an event that the field value has changed,
            # so that a parent can react appropriately
            evt = dEvents.dEvent(dEvents.EVT_FIELDCHANGED, self.GetId())
            self.GetEventHandler().ProcessEvent(evt)
            
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
   
    def onEvent(self, event):
        ''' onEvent(event), called by the event handlers in the individual
            widgets. This allows the Dabo framework to be guaranteed the
            opportunity to respond to the event, and to smartly pass 
            control over to the user's subclassed widgets. We'll need 
            this short-circuiting approach when it comes time to add in 
            the database controlsource functionality. This also provides 
            a sane, generic, event handling approach for the Dabo framework. 
        '''
    
        object = event.GetEventObject()
        eventName = self._getEventNameFromIdentifier(event.GetEventType())

        if self.debug:
            print "Event Fired:", object.GetName(), eventName
    
        if type(eventName) == type(list()):
            # try to run the callback method:
            exec("object.%s(event)" % eventName[1])
        else:
            #print type(eventName)
            print "FIXME: No common.onEvent defined for event code %s" % eventName
    
        # subclasses have already handled the event, so we can call
        # Skip() here in the framework, leaving that detail hidden from
        # the user of the framework.
        event.Skip()
    
    def onValueRefresh(self, event): 
        ''' Ask the dForm for the current value of the field.'''
        form = self.FindWindowById(event.GetId())
        
        print "onValueRefresh received by %s" % (self.GetName(),)
        event.Skip()
    
    def _getEventNameFromIdentifier(self, Id):
        try:
            eventName = self.eventDict[Id]
        except KeyError:
            eventName = str(Id)
        return eventName 
    
    def _getEventDict(self):
        ''' The eventDict dictionary maps the integer event codes
            back to the wx names for the events, as well as the names
            of the callback methods, allowing the callback names to be
            defined here, but once.'''
            
        eventDict = {
                        10020: ["EVT_TEXT",             "OnText"],
                        10031: ["EVT_BUTTON",           "OnButton"],
                        10046: ["EVT_SPINCTRL",         "OnSpin"],
                        10056: ["EVT_ENTER_WINDOW",     "OnEnterWindow"],
                        10057: ["EVT_LEAVE_WINDOW",     "OnLeaveWindow"],
                        10061: ["EVT_SET_FOCUS",        "OnSetFocus"],
                        10062: ["EVT_KILL_FOCUS",       "OnKillFocus"]
                    } 
    
        return eventDict                     
