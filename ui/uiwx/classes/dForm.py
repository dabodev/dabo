import wx, dEvents, dControlMixin, dDataControlMixin
from dFormMixin import dFormMixin
from dPageFrame import dPageFrame
from dPage import *
import dabo.dConstants as k
from dMessageBox import *

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
        wx.Frame.__init__(self, parent, -1, "", (-1,-1), (-1,-1), 
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
        
        self._setupResources(resourceString)

        self.CreateStatusBar()
        
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.setupPageFrame()
        self.GetSizer().Layout()
        
    def EVT_VALUEREFRESH(win, id, func):
        win.Connect(id, -1, dEvents.EVT_VALUEREFRESH, func)
    
    def _appendToMenu(self, menu, caption, function):
        menuId = wx.NewId()
        menu.Append(menuId, caption)
        wx.EVT_MENU(self, menuId, function)
        
    def getMenu(self):
        menu = dFormMixin.getMenu(self)
        
        self._appendToMenu(menu, "Set Selection Criteria\tAlt+1", 
                          self.onSetSelectionCriteria)
        self._appendToMenu(menu, "Browse Records\tAlt+2", 
                          self.onBrowseRecords)
        self._appendToMenu(menu, "Edit Current Record\tAlt+3", 
                          self.onEditCurrentRecord)
        menu.AppendSeparator()
        
        self._appendToMenu(menu, "Requery\tCtrl+R", 
                          self.onRequery)
        self._appendToMenu(menu, "Save Changes\tCtrl+S", 
                          self.onSave)
        self._appendToMenu(menu, "Cancel Changes", 
                          self.onCancel)
        menu.AppendSeparator()
        
        self._appendToMenu(menu, "Select First Record", 
                          self.onFirst)
        self._appendToMenu(menu, "Select Prior Record\tCtrl+,", 
                          self.onPrior)
        self._appendToMenu(menu, "Select Next Record\tCtrl+.", 
                          self.onNext)
        self._appendToMenu(menu, "Select Last Record", 
                          self.onLast)
        menu.AppendSeparator()
        self._appendToMenu(menu, "New Record\tCtrl+N", 
                self.onNew)
        self._appendToMenu(menu, "Delete Current Record", 
                self.onDelete)

        return menu
        
    def setupMenu(self):
        self.SetMenuBar(wx.MenuBar())
        self.GetMenuBar().Append(self.getMenu(), "&Navigation")
        wx.EVT_MENU_OPEN(self, self.onOpenMenu)
        
    def onOpenMenu(self, event):
        menu = event.GetEventObject()
        if self.bizobjs[self.getPrimaryBizobj()].getRowCount() < 0:
            # disable all menu items except for Requery. (I'd like
            # to get some sort of "skip for" functionality build into 
            # our menus, but that will wait.).
            for item in menu.GetMenuItems():
                if item.GetText() != "Requery":
                    item.Enable(False)
        else:
            # Enable all menu items
            for item in menu.GetMenuItems():
                item.Enable(True)            

    def addBizobj(self, bizobj):
        ''' dForm.addBizobj(bizobj) -> None
        
            Add the passed bizobj reference to this form. Make
            this bizobj the form's primary bizobj if it is the
            first bizobj to be added.
        '''
        self.bizobjs[bizobj.dataSource] = bizobj
        if len(self.bizobjs) == 1:
            self.setPrimaryBizobj(bizobj.dataSource)
        if self.debug:
            print "added bizobj with dataSource of %s" % bizobj.dataSource
        self.SetStatusText("Bizobj '%s' added." % bizobj.dataSource)
        
    def getPrimaryBizobj(self):
        return self._primaryBizobj
    
    def setPrimaryBizobj(self, dataSource):
        try:
            bo = self.bizobjs[dataSource]
        except KeyError:
            bo = None
        if bo:
            self._primaryBizobj = dataSource
            self.setupMenu()
        else:
            print "bizobj for data source %s does not exist." % dataSource
            
    def addControl(self, control):
        ''' dForm.addControl(control) -> None
        
            Add the passed dControl reference to this form.
            Normally this happens automatically, when the control
            is instantiated with the dForm as the parent.
        '''
        self.dControls[control.GetName()] = control
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
            biz = self.bizobjs[self.getPrimaryBizobj()]
            response = biz.first()
            if self.debug:
                print response
            if response == k.FILE_OK:
                self.SetStatusText(self.getCurrentRecordText())
        else:
            if self.debug:
                print "in dForm.first(): No bizobjs defined."
        self.refreshControls()
    
    def last(self):
        ''' dForm.last() --> None
        
            Ask the primary bizobj to move to the last record.
        '''
        if self.bizobjs:
            biz = self.bizobjs[self.getPrimaryBizobj()]
            response = biz.last()
            if self.debug: 
                print response
            if response == k.FILE_OK:
                self.SetStatusText(self.getCurrentRecordText())
        else:
            if self.debug:
                print "in dForm.first(): No bizobjs defined."
        self.refreshControls()
        
    def prior(self):
        ''' dForm.prior() --> None
        
            Ask the primary bizobj to move to the previous record.
        '''
        if self.bizobjs:
            biz = self.bizobjs[self.getPrimaryBizobj()]
            response = biz.prior()
            if self.debug:
                print response
            statusText = self.getCurrentRecordText()
            if response == k.FILE_BOF:
                statusText += " (BOF)"
            self.SetStatusText(statusText)
        else:
            if self.debug:
                print "in dForm.first(): No bizobjs defined."
        self.refreshControls()
        
    def next(self):
        ''' dForm.next(bizobj) --> None
        
            Ask the primary bizobj to move to the next record.
        '''
        if self.bizobjs:
            biz = self.bizobjs[self.getPrimaryBizobj()]
            response = biz.next()
            if self.debug:
                print response
            statusText = self.getCurrentRecordText()
            if response == k.FILE_EOF:
                statusText += " (EOF)"
            self.SetStatusText(statusText)
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
            self.SetStatusText("Changes to %s saved." % (
                    self.saveAllRows and "all records" or "current record",))
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
            self.SetStatusText("Changes to %s cancelled." % (
                    self.saveAllRows and "all records" or "current record",))
            self.refreshControls()
        else:
            if self.debug:
                print "Cancel failed with response: %s" % response
                print bizobj.getErrorMsg()
            ### TODO: What should be done here? Raise an exception?
            ###       Prompt the user for a response?
    
    def onRequery(self, event):
        self.requery()
        self.Raise()
        event.Skip()
                
    def requery(self):
        ''' dForm.requery() -> None
        
            Ask the primary bizobj to requery, and if successful refresh 
            the contained controls.
        '''
        import time
        
        start = time.time()
        response = self.getBizobj().requery()
        stop = round(time.time() - start, 3)
        
        if response == k.FILE_OK:
            if self.debug:
                print "Requery successful."
            self.SetStatusText("%s record%sselected in %s second%s" % (
                    self.getBizobj().getRowCount(), 
                    self.getBizobj().getRowCount() == 1 and " " or "s ",
                    stop,
                    stop == 1 and "." or "s."))
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
        if dAreYouSure("This will delete the current record, and cannot "
                        "be cancelled.\n\n Are you sure you want to do this?",
                        defaultNo=True):
            response = bizobj.delete()
            if response == k.FILE_OK:
                if self.debug:
                    print "Delete successful."
                self.SetStatusText("Record Deleted.")
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
        if dAreYouSure("This will delete all records in the recordset, and cannot "
                        "be cancelled.\n\n Are you sure you want to do this?",
                        defaultNo=True):
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
            statusText = self.getCurrentRecordText()
            self.SetStatusText(statusText)
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
            dataSource = self.getPrimaryBizobj()
        try:
            return self.bizobjs[dataSource]
        except KeyError:
            return None
            
    def setupPageFrame(self):
        ''' dForm.setupPageFrame() -> 
        
            Default behavior is to set up a 3-page pageframe
            with 'Select', 'Browse', and 'Edit' pages.
            User may override and/or extend in subclasses
            and overriding self.beforeSetupPageFrame(), 
            self.setupPageFrame, and/or self.afterSetupPageFrame().
        '''
        if self.beforeSetupPageFrame():
            self.pageFrame = dPageFrame(self)
            nbSizer = wx.NotebookSizer(self.pageFrame)
            self.GetSizer().Add(nbSizer, 1, wx.EXPAND)
            self.afterSetupPageFrame()
        
    def beforeSetupPageFrame(self): return True
    def afterSetupPageFrame(self): pass

    def onSetSelectionCriteria(self, event):
        self.pageFrame.SetSelection(0)
        
    def onBrowseRecords(self, event):
        self.pageFrame.SetSelection(1)
        
    def onEditCurrentRecord(self, event):
        self.pageFrame.SetSelection(2)
            
    def onFirst(self, event): self.first()
    def onPrior(self, event): self.prior()
    def onNext(self, event): self.next()
    def onLast(self, event): self.last()
    def onSave(self, event): self.save()
    def onCancel(self, event): self.cancel()
    def onNew(self, event): self.new()
    def onDelete(self, event): self.delete()
        
    def addVCR(self):
        ''' dForm.addVCR() -> None
        
            Add a VCR data nav control to the form -- temporary
            until we get dToolbar working.
        '''
        bs = wx.BoxSizer(wx.HORIZONTAL)
        import dVCR

        vcr = dVCR.dVCR(self)
        bs.Add(vcr, 1, wx.ALL, 0)
        self.GetSizer().Add(bs, 0, wx.EXPAND)
        self.GetSizer().Layout()

    def getCurrentRecordText(self):
        return "Record %s/%s" % (self.getBizobj().getRowNumber()+1,
                                    self.getBizobj().getRowCount())
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
