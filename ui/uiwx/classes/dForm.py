import wx, dEvents, dControlMixin, dDataControlMixin

class dForm(wx.Frame):
    def __init__(self, frame=None, resourceString=None):
        wx.Frame.__init__(self, frame, -1, "")
        self.SetName("dForm")
        self.SetLabel("dForm")
        self.debug = False
        
        self.bizobjs = []
        self.primaryBizobj = 0
        self.bizobjNames = {}
        
        self.dControls = []
        self._resourceString = resourceString
        
        self.setupResources()
            
    def setupResources(self):
        ''' Read from the resource file for this dForm,
            instantiating the contained controls and
            nonvisible objects, and setting properties
            of this dForm.
            
            As we haven't even defined our resource file
            format yet, this is just a stub.
        '''
        rs = self._resourceString
        
    def EVT_VALUEREFRESH(win, id, func):
        win.Connect(id, -1, dEvents.EVT_VALUEREFRESH, func)
    
    def addBizobj(self, bizobj):
        ''' Add the passed dBizobj reference to this form. '''
        self.bizobjs.append(bizobj)
        self.bizobjNames[bizobj.dataSource] = len(self.bizobjs) - 1
        print "added bizobj with dataSource of %s" % bizobj.dataSource
        
    def addControl(self, control):
        ''' Add the passed dControl reference to this form.
        
            This happens pretty much behind the scenes, from
            dControlMixin.__init__().
        '''
        self.dControls.append(control)
        print "added control %s" % control.GetName()
        
        # Set up the frame to receive the notification that 
        # the field value changed, and the object to receive
        # the notification from the form that it's time to 
        # refresh its value.
        if isinstance(control, dDataControlMixin.dDataControlMixin):
            dDataControlMixin.dDataControlMixin.EVT_FIELDCHANGED(control, 
                            control.GetId(), self.onFieldChanged)
            dForm.EVT_VALUEREFRESH(self, self.GetId(), control.onValueRefresh)
        
    def onFieldChanged(self, event):
        ''' A control is saying that its value has changed. Not sure if
            this event callback is needed at all, actually, as the appropriate
            action has already been taken in self.setFieldVal() directly.
        '''
        control = self.FindWindowById(event.GetId())
        if self.debug:
            print "\nEvent onFieldChanged received by %s.\n"\
                "     Control: %s \n" \
                "  dataSource: %s \n" \
                "   dataField: %s \n" \
                "       Value: %s \n" % (self.GetName(), 
                                    control.GetName(), 
                                    control.dataSource,
                                    control.dataField,
                                    control.GetValue())
       
    def refreshControls(self):
        ''' Raise EVT_VALUEREFRESH which will be caught by all
            registered controls. 
        '''
        evt = dEvents.dEvent(dEvents.EVT_VALUEREFRESH, self.GetId())
        self.GetEventHandler().ProcessEvent(evt)

    def first(self):
        if self.bizobjs:
            biz = self.bizobjs[self.primaryBizobj]
            response = biz.first()
            print response
        else:
            print "in dForm.first(): No bizobjs defined."
        self.refreshControls()
    
    def last(self):
        if self.bizobjs:
            biz = self.bizobjs[self.primaryBizobj]
            response = biz.last()
            print response
        else:
            print "in dForm.first(): No bizobjs defined."
        self.refreshControls()
        
    def prior(self):
        if self.bizobjs:
            biz = self.bizobjs[self.primaryBizobj]
            response = biz.prior()
            print response
        else:
            print "in dForm.first(): No bizobjs defined."
        self.refreshControls()
        
    def next(self):
        if self.bizobjs:
            biz = self.bizobjs[self.primaryBizobj]
            response = biz.next()
            print response
        else:
            print "in dForm.first(): No bizobjs defined."
        self.refreshControls()
    
    def getFieldVal(self, dataSource, dataField):
        ''' A dControl wants to know what its value should be. '''
        bizobj = self.getBizobj(dataSource)
        return bizobj.getFieldVal(dataField)
    
    def setFieldVal(self, dataSource, dataField, value):
        ''' A dControl wants to update the value in the bizobj. '''
        bizobj = self.getBizobj(dataSource)
        return bizobj.setFieldVal(dataField, value)

    def getBizobj(self, dataSource):
        return self.bizobjs[self.bizobjNames[dataSource]]
            
if __name__ == "__main__":
    import test
    test.Test().runTest(dForm)
