import wx, dEvents
import dFormMixin as fm
import dabo.dError as dError
import dabo.dConstants as k
import dMessageBox, dProgressDialog
from dabo.dLocalize import _

# Different platforms expect different frame types. Notably,
# most users on Windows expect and prefer the MDI parent/child
# type frames.
if wx.Platform == '__WXMSW__':
    wxFrameClass = wx.MDIChildFrame
else:
    wxFrameClass = wx.Frame


class dForm(wxFrameClass, fm.dFormMixin):
    ''' Create a dForm object, which is a bizobj-aware form.
        
    dForm knows how to handle one or more dBizobjs, providing proxy methods 
    like next(), last(), save(), and requery().
    '''

    def __init__(self, parent=None, name="dForm", resourceString=None):
        if parent:
            style = wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT
        else:
            style = wx.DEFAULT_FRAME_STYLE
        wxFrameClass.__init__(self, parent, -1, "", style=style)

        self.Name = name
        self.Caption = name
        
        if parent:        
            dApp = parent.dApp
        else:
            dApp = None
        fm.dFormMixin.__init__(self, dApp)
        
        self.debug = False
        
        self.bizobjs = {}
        self._primaryBizobj = None
        
        self.SaveAllRows = True    # Default should come from app
        self.AskToSave = True      # Display 'save changes?' prompt?
        
        self.dControls = {}
        
        self._setupResources(resourceString)

        if not isinstance(self, wx.MDIChildFrame):
            self.CreateStatusBar()
        
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.GetSizer().Layout()
        
        
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
        self.setStatusText("Bizobj '%s' %s." % (bizobj.dataSource, _("added")))
        
        
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
        EVT_VALUEREFRESH = wx.PyEventBinder(dEvents.EVT_VALUEREFRESH, 0)
        EVT_ROWNUMCHANGED = wx.PyEventBinder(dEvents.EVT_ROWNUMCHANGED, 0)    

        self.dControls[control.GetName()] = control
        if self.debug:
            print "added control %s which has the following properties:" % control.GetName()
            for prop in control.getPropertyList():
                print "  %s: %s" % (prop, eval("control.%s" % prop))
        
        # Set up the control to receive the notification 
        # from the form that it's time to refresh its value,
        # but only if the control is set up to receive these
        # notifications (if it has a onValueRefresh Method).
        try:
            func = control.onValueRefresh
        except AttributeError:
            func = None
        if func:
            self.Bind(EVT_VALUEREFRESH, func)
        
        # Set up the control to receive the notification 
        # from the form that that the row number changed,
        # but only if the control is set up to receive these
        # notifications (if it has a onRowNumChanged Method).
        try:
            func = control.onRowNumChanged
        except AttributeError:
            func = None
        if func:
            self.Bind(EVT_ROWNUMCHANGED, func)

            
    def refreshControls(self):
        ''' Refresh the value of all contained dControls.
        
        Raises EVT_VALUEREFRESH which will be caught by all dControls, who will
        in turn refresh themselves with the current value of the field in the
        bizobj. 
        '''
        evt = dEvents.dEvent(dEvents.EVT_VALUEREFRESH, self.GetId())
        self.GetEventHandler().ProcessEvent(evt)
        self.setStatusText(self.getCurrentRecordText())


    def _moveRecordPointer(self, func, dataSource=None):
        ''' Move the record pointer using the specified function.
        '''
        self.activeControlValid()
        try:
            response = func()
        except dError.NoRecordsError:
            self.setStatusText(_("No records in dataset."))
        else:
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
        try:
            self._moveRecordPointer(self.getBizobj(dataSource).prior, dataSource)
        except dError.BeginningOfFileError:
            self.setStatusText(self.getCurrentRecordText(dataSource) + " (BOF)")
        
    def next(self, dataSource=None):
        ''' Ask the bizobj to move to the next record.
        '''
        try:
            self._moveRecordPointer(self.getBizobj(dataSource).next, dataSource)
        except dError.EndOfFileError:
            self.setStatusText(self.getCurrentRecordText(dataSource) + " (EOF)")
    
        
    def save(self, dataSource=None):
        ''' Ask the bizobj to commit its changes to the backend.
        '''
        self.activeControlValid()
        bizobj = self.getBizobj(dataSource)
        
        try:
            bizobj.save(allRows=self.SaveAllRows)
            if self.debug:
                print "Save successful."
            self.setStatusText(_("Changes to %s saved." % (
                    self.SaveAllRows and "all records" or "current record",)))
        except dError.BusinessRuleViolation, e:
            self.setStatusText(_("Save failed."))
            dMessageBox.stop("%s:\n\n%s" % (_("Save Failed:"), _(str(e))))
    
            
    def cancel(self, dataSource=None):
        ''' Ask the bizobj to cancel its changes.
        
        This will revert back to the state of the records when they were last
        requeried or saved.
        '''
        self.activeControlValid()
        bizobj = self.getBizobj(dataSource)
        
        try:
            bizobj.cancel(allRows=self.SaveAllRows)
            if self.debug:
                print "Cancel successful."
            self.setStatusText(_("Changes to %s canceled." % (
                    self.SaveAllRows and "all records" or "current record",)))
            self.refreshControls()
        except dError.dError, e:
            if self.debug:
                print "Cancel failed with response: %s" % str(e)
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
        
        if bizobj.isChanged(allRows=True) and self.AskToSave:
            response = dMessageBox.areYouSure(_("Do you wish to save your changes?"),
                                              cancelButton=True)
            
            if response == None:    # cancel
                return
            elif response == True:  # yes
                self.save(dataSource=dataSource)
            
        self.setStatusText(_("Please wait... requerying dataset..."))
        start = time.time()
        
        try:
            response = dProgressDialog.displayAfterWait(self, 2, bizobj.requery)
            stop = round(time.time() - start, 3)
            if self.debug:
                print "Requery successful."
            self.setStatusText(_("%s record%sselected in %s second%s" % (
                    bizobj.getRowCount(), 
                    bizobj.getRowCount() == 1 and " " or "s ",
                    stop,
                    stop == 1 and "." or "s.")))
            self.refreshControls()
            
            # Notify listeners that the row number changed:
            evt = dEvents.dEvent(dEvents.EVT_ROWNUMCHANGED, self.GetId())
            self.GetEventHandler().ProcessEvent(evt)

        except dError.dError, e:
            if self.debug:
                print "Requery failed with response: %s" % str(e)
            ### TODO: What should be done here? Raise an exception?
            ###       Prompt the user for a response?

                                    
    def delete(self, dataSource=None, message=None):
        ''' Ask the bizobj to delete the current record.
        '''
        self.activeControlValid()
        bizobj = self.getBizobj(dataSource)
        if not message:
            message = _("This will delete the current record, and cannot "
                          "be canceled.\n\n Are you sure you want to do this?")
        if dMessageBox.areYouSure(message, defaultNo=True):
            try:
                bizobj.delete()
                if self.debug:
                    print "Delete successful."
                self.setStatusText(_("Record Deleted."))
                self.refreshControls()
                # Notify listeners that the row number changed:
                evt = dEvents.dEvent(dEvents.EVT_ROWNUMCHANGED, self.GetId())
                self.GetEventHandler().ProcessEvent(evt)
            except dError.dError, e:
                if self.debug:
                    print "Delete failed with response: %s" % str(e)
                ### TODO: What should be done here? Raise an exception?
                ###       Prompt the user for a response?
        
                
    def deleteAll(self, dataSource=None, message=None):
        ''' Ask the primary bizobj to delete all records from the recordset.
        '''
        self.activeControlValid()
        bizobj = self.getBizobj(dataSource)
        
        if not message:
            message = _("This will delete all records in the recordset, and cannot "
                          "be canceled.\n\n Are you sure you want to do this?")
                       
        if dMessageBox.areYouSure(message, defaultNo=True):
            try:
                bizobj.deleteAll()
                if self.debug:
                    print "Delete All successful."
                self.refreshControls()
                # Notify listeners that the row number changed:
                evt = dEvents.dEvent(dEvents.EVT_ROWNUMCHANGED, self.GetId())
                self.GetEventHandler().ProcessEvent(evt)
            except dError.dError, e:
                if self.debug:
                    print "Delete All failed with response: %s" % str(e)
                ### TODO: What should be done here? Raise an exception?
                ###       Prompt the user for a response?
    
                
    def new(self, dataSource=None):
        ''' Ask the bizobj to add a new record to the recordset.
        '''
        self.activeControlValid()
        bizobj = self.getBizobj(dataSource)
        try:
            bizobj.new()
            if self.debug:
                print "New successful."
            statusText = self.getCurrentRecordText(dataSource)
            self.setStatusText(statusText)
            self.refreshControls()
            
            # Notify listeners that the row number changed:
            evt = dEvents.dEvent(dEvents.EVT_ROWNUMCHANGED, self.GetId())
            self.GetEventHandler().ProcessEvent(evt)
            
            self.afterNew()
            
        except dError.dError, e:
            dMessageBox.stop(_("Add new record failed with response:\n\n%s" % str(e)))

    
    def afterNew(self):
        ''' Called after a new record is successfully added to the dataset.
        
        Override in subclasses for desired behavior.
        '''
        pass
        
        
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
        rowCount = bizobj.getRowCount()
        if rowCount > 0:
            rowNumber = bizobj.getRowNumber()+1
        else:
            rowNumber = 0
        return _("Record " ) + ("%s/%s" % (rowNumber, rowCount))
    
        
    def activeControlValid(self):
        ''' Force the control-with-focus to fire its KillFocus code.
        
        The bizobj will only get its field updated during the control's 
        KillFocus code. This function effectively commands that update to
        happen before it would have otherwise occurred.
        '''
        controlWithFocus = self.FindFocus()
        if controlWithFocus:
            try:
                controlWithFocus.flushValue()
            except AttributeError:
                # controlWithFocus may not be data-aware
                pass
        
                            
    def _setupResources(self, resourceString):
        ''' Set up the objects of this form based on the resource string.
        '''
        
        # As we haven't even defined our resource file
        # format yet, this is just a stub.
        pass
    
        
    # Property get/set/del functions follow.
    def _getSaveAllRows(self):
        return self._SaveAllRows
    def _setSaveAllRows(self, value):
        self._SaveAllRows = bool(value)
        
    def _getAskToSave(self):
        return self._AskToSave
    def _setAskToSave(self, value):
        self._AskToSave = bool(value)
        
    # Property definitions:
    SaveAllRows = property(_getSaveAllRows, _setSaveAllRows, None, 
                    'Specifies whether dataset is row- or table-buffered. (bool)')
                    
    AskToSave = property(_getAskToSave, _setAskToSave, None, 
                    'Specifies whether a save prompt appears before the data is requeried. (bool)')

                    
if __name__ == "__main__":
    import test
    test.Test().runTest(dForm)
