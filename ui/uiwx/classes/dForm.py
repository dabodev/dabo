import wx, dEvents, dControlMixin, dDataControlMixin
from dFormMixin import dFormMixin
import dabo.dConstants as k
import dMessageBox, dProgressDialog

# Different platforms expect different frame types. Notably,
# most users on Windows expect and prefer the MDI parent/child
# type frames.
if wx.Platform == '__WXMSW__':      # Microsoft Windows
    wxFrameClass = wx.MDIChildFrame
else:
    wxFrameClass = wx.Frame
    
    
class dForm(wxFrameClass, dFormMixin):
    ''' Create a dForm object, which is a bizobj-aware form.
        
    dForm knows how to handle one or more dBizobjs, providing proxy methods 
    like next(), last(), save(), and requery().
    '''
   
    def __init__(self, parent=None, name="dForm", resourceString=None):
        wxFrameClass.__init__(self, parent, -1, "", (-1,-1), (-1,-1), 
                            wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        self.SetName(name)
        self.SetLabel(name)

        if parent:        
            dApp = parent.dApp
        else:
            dApp = None
        dFormMixin.__init__(self, dApp)
        
        self.debug = False
        
        self.bizobjs = {}
        self._primaryBizobj = None
        
        self.saveAllRows = True    # Default should come from app
        
        self.dControls = {}
        self.controlWithFocus = None
        
        self._setupResources(resourceString)

        if not isinstance(self, wx.MDIChildFrame):
            self.CreateStatusBar()
        
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.GetSizer().Layout()
        
        
    def EVT_VALUEREFRESH(win, id, func):
        win.Connect(id, -1, dEvents.EVT_VALUEREFRESH, func)
    
        
    def EVT_ROWNUMCHANGED(win, id, func):
        win.Connect(id, -1, dEvents.EVT_ROWNUMCHANGED, func)
    
        
    def addBizobj(self, bizobj):
        ''' Add a bizobj to this form.
        
        Make the bizobj the form's primary bizobj if it is the first bizobj to 
        be added.
        '''
        self.bizobjs[bizobj.dataSource] = bizobj
        if len(self.bizobjs) == 1:
            self.setPrimaryBizobj(bizobj.dataSource)
        if self.debug:
            print "added bizobj with dataSource of %s" % bizobj.dataSource
        self.setStatusText("Bizobj '%s' added." % bizobj.dataSource)
        
        
    def getPrimaryBizobj(self):
        return self._primaryBizobj
    
        
    def setPrimaryBizobj(self, dataSource):
        try:
            bo = self.bizobjs[dataSource]
        except KeyError:
            bo = None
        if bo:
            self._primaryBizobj = dataSource
            self.afterSetPrimaryBizobj()
        else:
            print "bizobj for data source %s does not exist." % dataSource
    
            
    def afterSetPrimaryBizobj(self):
        ''' Subclass hook.
        '''
        pass
            
            
    def addControl(self, control):
        ''' Add a control to this form.
        
        This happens automatically for dControls.
        '''
        self.dControls[control.GetName()] = control
        if self.debug:
            print "added control %s" % control.GetName()
        
        # Set up the control to receive the notification 
        # from the form that it's time to refresh its value,
        # but only if the control is set up to receive these
        # notifications (if it has a onValueRefresh Method).
        try:
            func = control.onValueRefresh
        except AttributeError:
            func = None
        if func:
            dForm.EVT_VALUEREFRESH(self, self.GetId(), func)
        
        # Set up the control to receive the notification 
        # from the form that that the row number changed,
        # but only if the control is set up to receive these
        # notifications (if it has a onRowNumChanged Method).
        try:
            func = control.onRowNumChanged
        except AttributeError:
            func = None
        if func:
            dForm.EVT_ROWNUMCHANGED(self, self.GetId(), func)

            
    def refreshControls(self):
        ''' Refresh the value of all contained dControls.
        
        Raises EVT_VALUEREFRESH which will be caught by all dControls, who will
        in turn refresh themselves with the current value of the field in the
        bizobj. 
        '''
        evt = dEvents.dEvent(dEvents.EVT_VALUEREFRESH, self.GetId())
        self.GetEventHandler().ProcessEvent(evt)


    def _moveRecordPointer(self, func, dataSource=None):
        ''' Move the record pointer using the specified function.
        '''
        self.activeControlValid()
        response = func()
        self.setStatusText(self.getCurrentRecordText(dataSource))

        # Notify listeners that the row number changed:
        evt = dEvents.dEvent(dEvents.EVT_ROWNUMCHANGED, self.GetId())
        self.GetEventHandler().ProcessEvent(evt)
        
        self.refreshControls()
        
                
    def first(self, dataSource=None):
        ''' Ask the bizobj to move to the first record.
        '''
        self._moveRecordPointer(self.getBizobj(dataSource).first, dataSource)
    
        
    def last(self, dataSource=None):
        ''' Ask the bizobj to move to the last record.
        '''
        self._moveRecordPointer(self.getBizobj(dataSource).last, dataSource)
        
        
    def prior(self, dataSource=None):
        ''' Ask the bizobj to move to the previous record.
        '''
        self._moveRecordPointer(self.getBizobj(dataSource).prior, dataSource)
        
        
    def next(self, dataSource=None):
        ''' Ask the bizobj to move to the next record.
        '''
        self._moveRecordPointer(self.getBizobj(dataSource).next, dataSource)
    
        
    def save(self, dataSource=None):
        ''' Ask the bizobj to commit its changes to the backend.
        '''
        self.activeControlValid()
        bizobj = self.getBizobj(dataSource)
        response = bizobj.save(allRows=self.saveAllRows)
        if response == k.FILE_OK:
            if self.debug:
                print "Save successful."
            self.setStatusText("Changes to %s saved." % (
                    self.saveAllRows and "all records" or "current record",))
        else:
            self.setStatusText("Save failed.")
            dMessageBox.stop("Save failed:\n\n%s" % bizobj.getErrorMsg())
    
            
    def cancel(self, dataSource=None):
        ''' Ask the bizobj to cancel its changes.
        
        This will revert back to the state of the records when they were last
        requeried or saved.
        '''
        self.activeControlValid()
        bizobj = self.getBizobj(dataSource)
        response = bizobj.cancel(allRows=self.saveAllRows)
        if response == k.FILE_OK:
            if self.debug:
                print "Cancel successful."
            self.setStatusText("Changes to %s cancelled." % (
                    self.saveAllRows and "all records" or "current record",))
            self.refreshControls()
        else:
            if self.debug:
                print "Cancel failed with response: %s" % response
                print bizobj.getErrorMsg()
            ### TODO: What should be done here? Raise an exception?
            ###       Prompt the user for a response?
    
            
    def onRequery(self, event):
        ''' Occurs when an EVT_MENU event is received by this form.
        '''
        self.requery()
        self.Raise()
        event.Skip()
           
             
    def requery(self, dataSource=None):
        ''' Ask the bizobj to requery.
        '''
        import time
        
        self.activeControlValid()
        bizobj = self.getBizobj(dataSource)
        
        self.setStatusText("Please wait... requerying dataset...")
        start = time.time()
        response = dProgressDialog.displayAfterWait(self, 2, bizobj.requery)
        stop = round(time.time() - start, 3)
        
        if response == k.FILE_OK:
            if self.debug:
                print "Requery successful."
            self.setStatusText("%s record%sselected in %s second%s" % (
                    bizobj.getRowCount(), 
                    bizobj.getRowCount() == 1 and " " or "s ",
                    stop,
                    stop == 1 and "." or "s."))
            self.refreshControls()
            
            # Notify listeners that the row number changed:
            evt = dEvents.dEvent(dEvents.EVT_ROWNUMCHANGED, self.GetId())
            self.GetEventHandler().ProcessEvent(evt)
        else:
            if self.debug:
                print "Requery failed with response: %s" % response
                print bizobj.getErrorMsg()
            ### TODO: What should be done here? Raise an exception?
            ###       Prompt the user for a response?

                                    
    def delete(self, dataSource=None, message=None):
        ''' Ask the bizobj to delete the current record.
        '''
        self.activeControlValid()
        bizobj = self.getBizobj(dataSource)
        if not message:
            message = loc("This will delete the current record, and cannot "
                          "be cancelled.\n\n Are you sure you want to do this?")
        if dMessageBox.areYouSure(message, defaultNo=True):
            response = bizobj.delete()
            if response == k.FILE_OK:
                if self.debug:
                    print "Delete successful."
                self.setStatusText("Record Deleted.")
                self.refreshControls()
                # Notify listeners that the row number changed:
                evt = dEvents.dEvent(dEvents.EVT_ROWNUMCHANGED, self.GetId())
                self.GetEventHandler().ProcessEvent(evt)
            else:
                if self.debug:
                    print "Delete failed with response: %s" % response
                    print bizobj.getErrorMsg()
                ### TODO: What should be done here? Raise an exception?
                ###       Prompt the user for a response?
        
                
    def deleteAll(self, dataSource=None, message=None):
        ''' Ask the primary bizobj to delete all records from the recordset.
        '''
        self.activeControlValid()
        bizobj = self.getBizobj(dataSource)
        
        if not message:
            message = loc("This will delete all records in the recordset, and cannot "
                          "be cancelled.\n\n Are you sure you want to do this?")
                       
        if dMessageBox.areYouSure(message, defaultNo=True):
            response = bizobj.deleteAll()
            if response == k.FILE_OK:
                if self.debug:
                    print "Delete All successful."
                self.refreshControls()
                # Notify listeners that the row number changed:
                evt = dEvents.dEvent(dEvents.EVT_ROWNUMCHANGED, self.GetId())
                self.GetEventHandler().ProcessEvent(evt)
            else:
                if self.debug:
                    print "Delete All failed with response: %s" % response
                    print bizobj.getErrorMsg()
                ### TODO: What should be done here? Raise an exception?
                ###       Prompt the user for a response?
    
                
    def new(self, dataSource=None):
        ''' Ask the bizobj to add a new record to the recordset.
        '''
        self.activeControlValid()
        bizobj = self.getBizobj(dataSource)
        response = bizobj.new()
        if response == k.FILE_OK:
            if self.debug:
                print "New successful."
            statusText = self.getCurrentRecordText(dataSource)
            self.setStatusText(statusText)
            self.refreshControls()
            # Notify listeners that the row number changed:
            evt = dEvents.dEvent(dEvents.EVT_ROWNUMCHANGED, self.GetId())
            self.GetEventHandler().ProcessEvent(evt)
        else:
            if self.debug:
                print "New failed with response: %s" % response
                print bizobj.getErrorMsg()
            ### TODO: What should be done here? Raise an exception?
            ###       Prompt the user for a response?

    
    def getSQL(self, dataSource=None):
        ''' Get the current SQL from the bizobj.
        '''
        return self.getBizobj(dataSource).getSQL()
        
        
    def setSQL(self, sql, dataSource=None):
        ''' Set the SQL for the bizobj.
        '''
        self.getBizobj(dataSource).setSQL(sql)
            
        
    def getBizobj(self, dataSource=None):
        ''' Return the bizobj with the passed dataSource.
        
        If no dataSource is passed, getBizobj() will return the primary bizobj.
        '''
        if not dataSource:
            dataSource = self.getPrimaryBizobj()
        try:
            return self.bizobjs[dataSource]
        except KeyError:
            return None
            
            
    def onFirst(self, event): self.first()
    def onPrior(self, event): self.prior()
    def onNext(self, event): self.next()
    def onLast(self, event): self.last()
    def onSave(self, event): self.save()
    def onCancel(self, event): self.cancel()
    def onNew(self, event): self.new()
    def onDelete(self, event): self.delete()
        
    
    def getCurrentRecordText(self, dataSource=None):
        ''' Get the text to describe which record is current.
        '''
        bizobj = self.getBizobj(dataSource)
        rowNumber = bizobj.getRowNumber()+1
        rowCount = bizobj.getRowCount()
        if rowNumber == rowCount:
            postText = ' (EOF)'
        elif rowNumber == 1:
            postText = ' (BOF)'
        elif (rowNumber < 1 or rowNumber > rowCount):
            postText = ' (???)'
        else:
            postText = ''
        return "Record %s/%s%s" % (rowNumber, rowCount, postText)
    
        
    def activeControlValid(self):
        ''' Force the control-with-focus to fire its KillFocus code.
        
        The bizobj will only get its field updated during the control's 
        KillFocus code. This function effectively commands that update to
        happen before it would have otherwise occurred.
        '''
        try:
            controlWithFocus = self.controlWithFocus
        except AttributeError:
            controlWithFocus = None
        if controlWithFocus:
            controlWithFocus.flushValue()
        
                            
    def _setupResources(self, resourceString):
        ''' Set up the objects of this form based on the resource string.
        '''
        
        # As we haven't even defined our resource file
        # format yet, this is just a stub.
        pass
    
        
if __name__ == "__main__":
    import test
    test.Test().runTest(dForm)
