import wx, dEvents, dControlMixin, dDataControlMixin

class dForm(wx.Frame):
    def __init__(self, frame=None, resourceString=None):
        wx.Frame.__init__(self, frame, -1, "")
        self.SetName("dForm")
        self.SetLabel("dForm")
        self.debug = False
        
        self.bizobjs = {}
        self.primaryBizobj = None
        
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
        self.bizobjs[bizobj.dataSource] = bizobj
        if len(self.bizobjs) == 1:
            # This is the first bizobj added: make it the 
            # primary bizobj. If there will be more than
            # one bizobj for this dForm, and the first one
            # shouldn't be primary, it will be up to the 
            # user to change it manually.
            self.primaryBizobj = bizobj.dataSource
        print "added bizobj with dataSource of %s" % bizobj.dataSource
        
    def addControl(self, control):
        ''' Add the passed dControl reference to this form.
        
            This happens pretty much behind the scenes, from
            dControlMixin.__init__().
        '''
        self.dControls.append(control)
        print "added control %s" % control.GetName()
        
        # Set up the object to receive the notification 
        # from the form that it's time to refresh its value.
        if isinstance(control, dDataControlMixin.dDataControlMixin):
            dForm.EVT_VALUEREFRESH(self, self.GetId(), control.onValueRefresh)
        
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
    
    def getBizobj(self, dataSource):
        try:
            return self.bizobjs[dataSource]
        except KeyError:
            return None
            
if __name__ == "__main__":
    import test
    test.Test().runTest(dForm)
