import wx, dEvents, dControlMixin, dDataControlMixin
from dFormMixin import dFormMixin
import dabo.dConstants as k

class dForm(wx.Frame, dFormMixin):
    ''' dabo.ui.uiwx.dForm() --> dForm
    
        Create a dForm object, which can contain other
        dControls, such as dTextBox, dPageFrame, and dGrid.
        
        dForm knows how to handle one or more dBizobjs,
        and provides proxy methods like next(), last(), 
        save(), and requery() which act on the primary
        bizobj.
    '''
    
    def __init__(self, parent=None, name="dForm", resourceString=None):
        wx.Frame.__init__(self, parent, -1, "")
        self.SetName(name)
        self.SetLabel(name)
        
        try:
            dApp = parent.dApp
        except:
            dApp = None
        
        dFormMixin.__init__(self, dApp)
        
        self.debug = False
        
        self.bizobjs = {}
        self.primaryBizobj = None
        
        self.saveAllRows = True    # Default should come from app
        
        self.dControls = []
        
        self._setupResources(resourceString)
    
    
    def EVT_VALUEREFRESH(win, id, func):
        win.Connect(id, -1, dEvents.EVT_VALUEREFRESH, func)
            
    
    def addBizobj(self, bizobj):
        ''' dForm.addBizobj(bizobj) -> None
        
            Add the passed bizobj reference to this form. Make
            this bizobj the form's primary bizobj if it is the
            first bizobj to be added.
        '''
        self.bizobjs[bizobj.dataSource] = bizobj
        if len(self.bizobjs) == 1:
            self.primaryBizobj = bizobj.dataSource
        if self.debug:
            print "added bizobj with dataSource of %s" % bizobj.dataSource
        
    def addControl(self, control):
        ''' dForm.addControl(control) -> None
        
            Add the passed dControl reference to this form.
            Normally this happens automatically, when the control
            is instantiated with the dForm as the parent.
        '''
        self.dControls.append(control)
        if self.debug:
            print "added control %s" % control.GetName()
        
        # Set up the control to receive the notification 
        # from the form that it's time to refresh its value,
        # but only if the control is data-aware.
        if isinstance(control, dDataControlMixin.dDataControlMixin):
            dForm.EVT_VALUEREFRESH(self, self.GetId(), control.onValueRefresh)
        
    
    def refreshControls(self):
        ''' dForm.refreshControls() -> None
        
            Raise EVT_VALUEREFRESH which will be caught by all
            registered controls so they can take action to refresh
            themselves. 
        '''
        evt = dEvents.dEvent(dEvents.EVT_VALUEREFRESH, self.GetId())
        self.GetEventHandler().ProcessEvent(evt)

        
    def first(self):
        ''' dForm.first() --> None
        
            Ask the primary bizobj to move to the first record.
        '''
        if self.bizobjs:
            biz = self.bizobjs[self.primaryBizobj]
            response = biz.first()
            if self.debug:
                print response
        else:
            if self.debug:
                print "in dForm.first(): No bizobjs defined."
        self.refreshControls()
    
    def last(self):
        ''' dForm.last() --> None
        
            Ask the primary bizobj to move to the last record.
        '''
        if self.bizobjs:
            biz = self.bizobjs[self.primaryBizobj]
            response = biz.last()
            if self.debug: 
                print response
        else:
            if self.debug:
                print "in dForm.first(): No bizobjs defined."
        self.refreshControls()
        
    def prior(self):
        ''' dForm.prior() --> None
        
            Ask the primary bizobj to move to the previous record.
        '''
        if self.bizobjs:
            biz = self.bizobjs[self.primaryBizobj]
            response = biz.prior()
            if self.debug:
                print response
        else:
            if self.debug:
                print "in dForm.first(): No bizobjs defined."
        self.refreshControls()
        
    def next(self):
        ''' dForm.next(bizobj) --> None
        
            Ask the primary bizobj to move to the next record.
        '''
        if self.bizobjs:
            biz = self.bizobjs[self.primaryBizobj]
            response = biz.next()
            if self.debug:
                print response
        else:
            if self.debug:
                print "in dForm.first(): No bizobjs defined."
        self.refreshControls()
    
        
    def save(self):
        ''' dForm.save() -> None
        
            Ask the primary bizobj to commit its changes to the 
            backend.
        '''
        bizobj = self.getBizobj()
        response = bizobj.save(allRows=self.saveAllRows)
        if response == k.FILE_OK:
            if self.debug:
                print "Save successful."
        else:
            if self.debug:
                print "Save failed with response: %s" % response
                print bizobj.getErrorMsg()
            ### TODO: What should be done here? Raise an exception?
            ###       Prompt the user for a response?
    
    def cancel(self):
        ''' dForm.save() -> None
        
            Ask the primary bizobj to cancel its changes, to 
            revert back to the state of the records when they
            were last requeried or saved.
        '''
        bizobj = self.getBizobj()
        response = bizobj.cancel(allRows=self.saveAllRows)
        if response == k.FILE_OK:
            if self.debug:
                print "Cancel successful."
            self.refreshControls()
        else:
            if self.debug:
                print "Cancel failed with response: %s" % response
                print bizobj.getErrorMsg()
            ### TODO: What should be done here? Raise an exception?
            ###       Prompt the user for a response?
            
    def requery(self):
        ''' dForm.requery() -> None
        
            Ask the primary bizobj to requery, and if successful refresh 
            the contained controls.
        '''
        bizobj = self.getBizobj()
        response = bizobj.requery()
        if response == k.FILE_OK:
            if self.debug:
                print "Requery successful."
            self.refreshControls()
        else:
            if self.debug:
                print "Requery failed with response: %s" % response
                print bizobj.getErrorMsg()
            ### TODO: What should be done here? Raise an exception?
            ###       Prompt the user for a response?
                        
    def delete(self):
        ''' dForm.delete() -> None
        
            Ask the primary bizobj to delete the current record from
            the recordset, and if successful refresh the contained 
            controls.
        '''
        bizobj = self.getBizobj()
        response = bizobj.delete()
        if response == k.FILE_OK:
            if self.debug:
                print "Delete successful."
            self.refreshControls()
        else:
            if self.debug:
                print "Delete failed with response: %s" % response
                print bizobj.getErrorMsg()
            ### TODO: What should be done here? Raise an exception?
            ###       Prompt the user for a response?
        
    def deleteAll(self):
        ''' dForm.deleteAll() -> None
        
            Ask the primary bizobj to delete all records from
            the recordset, and if successful refresh the contained 
            controls.
        '''
        bizobj = self.getBizobj()
        response = bizobj.deleteAll()
        if response == k.FILE_OK:
            if self.debug:
                print "Delete All successful."
            self.refreshControls()
        else:
            if self.debug:
                print "Delete All failed with response: %s" % response
                print bizobj.getErrorMsg()
            ### TODO: What should be done here? Raise an exception?
            ###       Prompt the user for a response?
    
    def new(self):
        ''' dForm.new() -> None
        
            Ask the primary bizobj to add a new record to 
            the recordset, and if successful refresh the 
            contained controls.
        '''
        bizobj = self.getBizobj()
        response = bizobj.new()
        if response == k.FILE_OK:
            if self.debug:
                print "New successful."
            self.refreshControls()
        else:
            if self.debug:
                print "New failed with response: %s" % response
                print bizobj.getErrorMsg()
            ### TODO: What should be done here? Raise an exception?
            ###       Prompt the user for a response?
    
    def getBizobj(self, dataSource=None):
        ''' dForm.getBizobj([dataSource]) -> bizobj or None
        
            Return the bizobj with the passed dataSource, or if
            no dataSource passed return the primary bizobj.
        '''
        if not dataSource:
            dataSource = self.primaryBizobj
        try:
            return self.bizobjs[dataSource]
        except KeyError:
            return None
            
    
    def _setupResources(self, resourceString):
        ''' dForm._setupResources(resourceString) -> None
        
            Read from resourceString, and instantiate the specified
            controls, set their properties, etc. The resource string
            probably originated as a resource file saved on disk.
        '''
        
        # As we haven't even defined our resource file
        # format yet, this is just a stub.
        pass
        
if __name__ == "__main__":
    import test
    test.Test().runTest(dForm)
