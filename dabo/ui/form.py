# -*- coding: utf-8 -*-
import sys
import time

import wx

from .. import application
from .. import biz
from .. import events
from .. import exceptions
from .. import settings
from .. import ui
from ..lib.utils import ustr
from ..localization import _
from . import dButton
from . import dFormMixin
from . import dSizer
from . import makeDynamicProperty

dabo_module = settings.get_dabo_package()


class BaseForm(dFormMixin):
    """
    Creates a bizobj-aware form.

    dForm knows how to handle one or more dBizobjs, providing proxy methods
    like next(), last(), save(), and requery().
    """

    def __init__(self, preClass, parent, properties, attProperties, *args, **kwargs):
        self.bizobjs = {}
        self._primaryBizobj = None
        self._dataUpdateDelay = 100
        self._rowNavigationDelay = 0

        # Use this for timing queries and other long-
        # running events
        self.stopWatch = wx.StopWatch()
        self.stopWatch.Pause()

        # Determines if the user is prompted to save changes when the form is closed
        # or a requery is about to happen.
        self._checkForChanges = True

        dFormMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

        # Used to override some cases where the status
        # text should be displayed despite other processes
        # trying to overwrite it
        self._holdStatusText = ""
        # Holds the dataSource passed to the method
        self.dataSourceParameter = None

    def _beforeSetProperties(self, props):
        if "UseSizers" in props and not hasattr(self, "UseSizers"):
            del props["UseSizers"]

    def _afterInit(self):
        self.Sizer = dSizer("vertical")
        self.Sizer.layout()
        super()._afterInit()
        if self.RequeryOnLoad:
            ui.callAfter(self.requery)

    def _beforeClose(self, evt=None):
        """
        See if there are any pending changes in the form, if the
        form is set for checking for this. If everything's OK, call the
        hook method.
        """
        ret = True
        if not self._isClosed:
            self.activeControlValid()
            ret = self.confirmChanges()
        if ret:
            ret = super()._beforeClose(evt)
        return ret

    def notifyUser(self, msg, title=None, severe=False, exception=None):
        """
        Displays an alert messagebox for the user. You can customize
        this in your own classes if you prefer a different display.
        """
        if exception and not settings.eatBizExceptions:
            raise exception
        if severe:
            func = ui.stop
        else:
            func = ui.info
        if title is None:
            title = _("Notice")
        func(message=msg, title=title)

    def update(self, interval=None):
        """
        Updates the contained controls with current values from the source.

        This method is called repeatedly from many different places during
        a single change in the UI, so by default the actual execution is cached
        using callAfterInterval(). The default interval is the value of the
        DataUpdateDelay property, which in turn defaults to 100 milliseconds. You
        can change that to suit your app needs by passing a different interval
        in milliseconds.

        Sometimes, though, you want to force immediate execution of the
        update. In these cases, pass an interval of 0 to this method, which
        means don't wait; execute now.
        """
        if interval is None:
            interval = self.DataUpdateDelay or 0
        if interval:
            ## Call update() after interval; send 0 to tell update to do it immediately.
            ui.callAfterInterval(interval, self.update, 0)
        else:
            try:
                super().update()
            except (RuntimeError, TypeError):
                # I think I'm dealing with a deadobject error. Sometimes getting:
                #   <type 'exceptions.TypeError'>: super(): obj must be an instance
                #   or subtype of type
                pass

    def confirmChanges(self, bizobjs=None):
        """
        Ask the user if they want to save changes, discard changes, or cancel.

        The user will be queried if the form's CheckForChanges property is True, and
        if there are any pending changes on the form's bizobjs as specified in either
        the 'bizobjs' parameter, or, if no parameter is sent, the return value of
        getBizobjsToCheck().

        If all the above are True, the dialog will be presented. "Yes" will cause
        all changes to be saved. "No" will discard any changes before proceeding
        with the operation that caused confirmChanges() to be called in the first
        place (e.g. a requery() or the form being closed). "Cancel" will not save
        any changes, but also cancel the requery or form close.

        See also: getBizobjsToCheck() method, CheckForChanges property.
        """
        if not self.CheckForChanges:
            # Don't bother checking
            return True
        if bizobjs is None:
            bizobjs = self.getBizobjsToCheck()
        if not isinstance(bizobjs, (list, tuple)):
            bizList = (bizobjs,)
        else:
            bizList = bizobjs
        changedBizList = []

        for biz_item in bizList:
            if biz_item and biz_item.isAnyChanged(withChildren=self.SaveChildren):
                changedBizList.append(biz_item)

        if changedBizList:
            queryMessage = self.getConfirmChangesQueryMessage(changedBizList)
            response = ui.areYouSure(queryMessage, parent=self)
            if response is None:  ## cancel
                # Don't let the form close, or requery happen
                return False
            elif response is True:  ## yes
                for biz_item in changedBizList:
                    self.save(dataSource=biz.DataSource)
            elif response is False:  ## no
                pass
                # why bother cancelling when the bizobj will just go away?
                # for biz_item in changedBizList:
                # if biz_item.RowCount:
                # self.cancel(dataSource=biz.DataSource)
        return True

    def getConfirmChangesQueryMessage(self, changedBizList):
        """
        Return the "Save Changes?" message for use in the query dialog.

        The default is to return "Do you wish to save your changes?". Subclasses
        can override with whatever message they want, possibly iterating the
        changed bizobj list to introspect the exact changes made to construct the
        message.
        """
        return _("Do you wish to save your changes?")

    def getBizobjsToCheck(self):
        """
        Return the list of bizobj's to check for changes during confirmChanges().

        The default behavior is to simply check the primary bizobj, however there
        may be cases in subclasses where a different bizobj may be checked, or even
        several. In those cases, override    this method and return a list of the
        required bizobjs.
        """
        return (self.PrimaryBizobj,)

    def addBizobj(self, bizobj):
        """
        Add a bizobj to this form.

        Make the bizobj the form's primary bizobj if it is the first bizobj to
        be added. For convenience, return the bizobj to the caller
        """
        self.bizobjs[bizobj.DataSource] = bizobj
        if len(self.bizobjs) == 1:
            self.PrimaryBizobj = bizobj
        self.updateStatusText("Bizobj '%s' %s." % (bizobj.DataSource, _("added")))
        return bizobj

    def afterSetPrimaryBizobj(self):
        """Subclass hook."""
        pass

    def moveToRowNumber(self, rowNumber, dataSource=None):
        """Move the record pointer to the specified row."""
        self.dataSourceParameter = dataSource
        if isinstance(dataSource, biz.dBizobj):
            bizobj = dataSource
        else:
            bizobj = self.getBizobj(dataSource)
        if bizobj is None:
            # Running in preview or some other non-live mode
            return
        return self._moveRecordPointer(
            bizobj.moveToRowNumber, dataSource=bizobj, rowNumber=rowNumber
        )

    def _afterPointerMoveUpdate(self, bizobj):
        self.update(0)
        self.refresh()
        # Notify listeners that the row number changed:
        self.raiseEvent(
            events.RowNumChanged,
            newRowNumber=bizobj.RowNumber,
            oldRowNumber=self.__oldRowNum,
            bizobj=bizobj,
        )
        self.afterPointerMove()

    def _moveRecordPointer(self, func, dataSource=None, *args, **kwargs):
        """Move the record pointer using the specified function."""
        self.dataSourceParameter = dataSource
        if isinstance(dataSource, biz.dBizobj):
            bizobj = dataSource
        else:
            bizobj = self.getBizobj(dataSource)
        oldRowNum = self.__oldRowNum = bizobj.RowNumber

        if self.activeControlValid() is False:
            # Field validation failed
            return False
        self.updateStatusText("%s..." % (self.getCurrentRecordText(),), immediate=True)
        err = self.beforePointerMove()
        if err:
            self.notifyUser(err)
            return False

        def bail(msg, meth=None, *args, **kwargs):
            if meth is None:
                meth = self.updateStatusText
            meth(msg, *args, **kwargs)

        try:
            response = func(*args, **kwargs)
        except exceptions.NoRecordsException:
            bail(_("No records in dataset."))
            return False
        except exceptions.BeginningOfFileException:
            bail(self.getCurrentRecordText(dataSource) + " (BOF)")
            return False
        except exceptions.EndOfFileException:
            bail(self.getCurrentRecordText(dataSource) + " (EOF)")
            return False
        except exceptions.dException as e:
            bail(ustr(e), meth=self.notifyUser, exception=e)
            return False
        else:
            if bizobj.RowNumber != oldRowNum:
                curTime = time.time()
                if curTime - getattr(self, "_lastNavigationTime", 0) > 0.5:
                    delay = 0
                else:
                    delay = self.RowNavigationDelay
                self._lastNavigationTime = curTime
                self._afterRowNavigation()
                self.raiseEvent(events.RowNavigation, biz=bizobj)
                if delay:
                    ui.callAfterInterval(delay, self._afterPointerMoveUpdate, bizobj)
                else:
                    self._afterPointerMoveUpdate(bizobj)
        return True

    def _afterRowNavigation(self):
        self.updateStatusText(self.getCurrentRecordText(), immediate=True)
        self.afterRowNavigation()

    def first(self, dataSource=None):
        """Ask the bizobj to move to the first record."""
        self.dataSourceParameter = dataSource
        bizobj = self.getBizobj(dataSource)
        if bizobj is None:
            # Running in preview or some other non-live mode
            return
        err = self.beforeFirst()
        if err:
            self.notifyUser(err)
            return
        self._moveRecordPointer(bizobj.first, dataSource)
        self.afterFirst()

    def last(self, dataSource=None):
        """Ask the bizobj to move to the last record."""
        self.dataSourceParameter = dataSource
        bizobj = self.getBizobj(dataSource)
        if bizobj is None:
            # Running in preview or some other non-live mode
            return
        err = self.beforeLast()
        if err:
            self.notifyUser(err)
            return
        self._moveRecordPointer(bizobj.last, dataSource)
        self.afterLast()

    def prior(self, dataSource=None):
        """Ask the bizobj to move to the previous record."""
        self.dataSourceParameter = dataSource
        bizobj = self.getBizobj(dataSource)
        if bizobj is None:
            # Running in preview or some other non-live mode
            return
        err = self.beforePrior()
        if err:
            self.notifyUser(err)
            return
        self._moveRecordPointer(bizobj.prior, dataSource)
        self.afterPrior()

    def next(self, dataSource=None):
        """Ask the bizobj to move to the next record."""
        self.dataSourceParameter = dataSource
        bizobj = self.getBizobj(dataSource)
        if bizobj is None:
            # Running in preview or some other non-live mode
            return
        err = self.beforeNext()
        if err:
            self.notifyUser(err)
            return
        self._moveRecordPointer(bizobj.__next__, dataSource)
        self.afterNext()

    def filter(self, dataSource=None, fld=None, expr=None, op="="):
        """Apply a filter to the bizobj's data."""
        self.dataSourceParameter = dataSource
        bizobj = self.getBizobj(dataSource)
        if bizobj is None:
            # Running in preview or some other non-live mode
            return
        # Make sure that they passed 'fld' and 'expr'
        if fld is None or expr is None:
            raise ValueError(
                _("Both 'fld' and 'expr' need to be supplied to the call to filter().")
            )
        err = self.beforeFilter()
        if err:
            self.notifyUser(err)
            return
        self._moveRecordPointer(bizobj.filter, dataSource, fld=fld, expr=expr, op=op)
        self.afterFilter()

    def removeFilter(self, dataSource=None):
        """Remove the most recently applied filter from the bizobj's data."""
        self.dataSourceParameter = dataSource
        bizobj = self.getBizobj(dataSource)
        if bizobj is None:
            # Running in preview or some other non-live mode
            return
        self._moveRecordPointer(bizobj.removeFilter, dataSource)

    def removeFilters(self, dataSource=None):
        """Remove all filters from the bizobj's data."""
        self.dataSourceParameter = dataSource
        bizobj = self.getBizobj(dataSource)
        if bizobj is None:
            # Running in preview or some other non-live mode
            return
        self._moveRecordPointer(bizobj.removeFilters, dataSource)

    def save(self, dataSource=None):
        """Ask the bizobj to commit its changes to the backend."""
        self.dataSourceParameter = dataSource
        bizobj = self.getBizobj(dataSource)
        if bizobj is None:
            # Running in preview or some other non-live mode
            return
        self.activeControlValid()

        err = self.beforeSave()
        if err:
            self.notifyUser(err)
            return False

        try:
            if self.SaveAllRows:
                bizobj.saveAll(saveTheChildren=self.SaveChildren)
            else:
                bizobj.save(saveTheChildren=self.SaveChildren)

            self.updateStatusText(
                _("Changes to %s saved.")
                % (self.SaveAllRows and "all records" or "current record",)
            )

        except exceptions.ConnectionLostException as e:
            msg = self._connectionLostMsg(ustr(e))
            self.notifyUser(msg, title=_("Data Connection Lost"), severe=True, exception=e)
            sys.exit()

        except exceptions.NoRecordsException as e:
            # No records were saved. No big deal; just let 'em know.
            self.updateStatusText(_("Nothing to save!"))
            return True

        except (exceptions.BusinessRuleViolation, exceptions.DBQueryException) as e:
            txt = _("Save Failed")
            self.updateStatusText(txt)
            msg = "%s:\n\n%s" % (txt, ustr(e))
            self.notifyUser(msg, severe=True, exception=e)
            return False

        self.afterSave()
        self.refresh()
        return True

    def cancel(self, dataSource=None, ignoreNoRecords=None):
        """
        Ask the bizobj to cancel its changes.

        This will revert back to the state of the records when they were last
        requeried or saved.
        """
        self.dataSourceParameter = dataSource
        bizobj = self.getBizobj(dataSource)
        if bizobj is None:
            # Running in preview or some other non-live mode
            return
        self.activeControlValid()
        if ignoreNoRecords is None:
            ignoreNoRecords = True

        err = self.beforeCancel()
        if err:
            self.notifyUser(err)
            return
        try:
            if self.SaveAllRows:
                bizobj.cancelAll(
                    ignoreNoRecords=ignoreNoRecords,
                    cancelTheChildren=self.CancelChildren,
                )
            else:
                bizobj.cancel(
                    ignoreNoRecords=ignoreNoRecords,
                    cancelTheChildren=self.CancelChildren,
                )
            self.update()
            self.updateStatusText(
                _("Changes to %s canceled.")
                % (self.SaveAllRows and "all records" or "current record",)
            )
        except exceptions.NoRecordsException as e:
            dabo_module.error(_("Cancel failed; no records to cancel."))
        except exceptions.dException as e:
            dabo_module.error(_("Cancel failed with response: %s") % e)
            self.notifyUser(ustr(e), title=_("Cancel Not Allowed"), exception=e)
        self.afterCancel()
        self.refresh()

    def onRequery(self, evt):
        """Occurs when an EVT_MENU event is received by this form."""
        self.requery()
        self.Raise()
        evt.Skip()

    def requery(self, dataSource=None):
        """Ask the bizobj to requery."""
        self.dataSourceParameter = dataSource
        ret = False
        bizobj = self.getBizobj(dataSource)
        if bizobj is None:
            # Running in preview or some other non-live mode
            return
        oldRowNumber = bizobj.RowNumber
        self.activeControlValid()

        err = self.beforeRequery()
        if err:
            self.notifyUser(err)
            return
        if not self.confirmChanges(bizobjs=bizobj):
            # A False from confirmChanges means "don't proceed"
            return

        ## A user-initiated requery should expire the cache on child bizobjs too:
        bizobj.expireCache()

        try:
            self.StatusText = _("Please wait... requerying dataset...")
            #            busy = ui.busyInfo(_("Please wait... requerying dataset..."))
            self.stopWatch.Start()
            #            response = dProgressDialog.displayAfterWait(self, 2, bizobj.requery)
            response = bizobj.requery()
            self.stopWatch.Pause()
            elapsed = round(self.stopWatch.Time() / 1000.0, 3)
            #            del busy
            self.update()

            newRowNumber = bizobj.RowNumber
            if newRowNumber != oldRowNumber:
                # Notify listeners that the row number changed:
                self.raiseEvent(
                    events.RowNumChanged,
                    newRowNumber=newRowNumber,
                    oldRowNumber=oldRowNumber,
                    bizobj=bizobj,
                )

            # We made it through without errors
            ret = True
            rc = bizobj.RowCount
            plcnt = bizobj.RowCount == 1 and " " or "s "
            plelap = elapsed == 1 and "." or "s."
            self.StatusText = (
                _("%(rc)s record%(plcnt)sselected in %(elapsed)s second%(plelap)s") % locals()
            )

        except exceptions.MissingPKException as e:
            self.notifyUser(ustr(e), title=_("Requery Failed"), severe=True, exception=e)
            self.StatusText = ""

        except exceptions.ConnectionLostException as e:
            msg = self._connectionLostMsg(ustr(e))
            self.notifyUser(msg, title=_("Data Connection Lost"), severe=True, exception=e)
            self.StatusText = ""
            sys.exit()

        except exceptions.DBQueryException as e:
            dabo_module.error(_("Database Execution failed with response: %s") % e)
            self.notifyUser(ustr(e), title=_("Database Action Failed"), severe=True, exception=e)
            self.StatusText = ""

        except exceptions.dException as e:
            dabo_module.error(_("Requery failed with response: %s") % e)
            self.notifyUser(ustr(e), title=_("Requery Not Allowed"), severe=True, exception=e)
            self.StatusText = ""

        self.afterRequery()
        self.refresh()
        return ret

    def delete(self, dataSource=None, message=None, prompt=True):
        """Ask the bizobj to delete the current record."""
        self.dataSourceParameter = dataSource
        bizobj = self.getBizobj(dataSource)
        if bizobj is None:
            # Running in preview or some other non-live mode
            return

        ds = bizobj.DataSource
        biz_caption = bizobj.Caption
        if not biz_caption:
            biz_caption = ds

        self.activeControlValid()

        if not bizobj.RowCount > 0:
            # Nothing to delete!
            self.updateStatusText(_("Nothing to delete!"))
            return

        err = self.beforeDelete()
        if err:
            self.notifyUser(err)
            return
        if message is None:
            message = (
                _(
                    "This will delete the current record from %s, and cannot "
                    "be canceled.\n\n Are you sure you want to do this?"
                )
                % biz_caption
            )
        if not prompt or ui.areYouSure(message, defaultNo=True, cancelButton=False):
            try:
                bizobj.delete()
                self.updateStatusText(_("Record Deleted."))
                # Notify listeners that the row number changed:
                self.raiseEvent(events.RowNumChanged)
            except exceptions.ConnectionLostException as e:
                msg = self._connectionLostMsg(ustr(e))
                self.notifyUser(msg, title=_("Data Connection Lost"), severe=True, exception=e)
                sys.exit()
            except exceptions.dException as e:
                msg = ustr(e)
                dabo_module.error(_("Delete failed with response: %s") % msg)
                self.notifyUser(msg, title=_("Deletion Not Allowed"), severe=True, exception=e)
            self.update()
            self.afterDelete()
            self.refresh()

    def deleteAll(self, dataSource=None, message=None):
        """Ask the primary bizobj to delete all records from the recordset."""
        self.dataSourceParameter = dataSource
        bizobj = self.getBizobj(dataSource)
        if bizobj is None:
            # Running in preview or some other non-live mode
            return
        self.activeControlValid()

        err = self.beforeDeleteAll()
        if err:
            self.notifyUser(err)
            return
        if not message:
            message = _(
                "This will delete all records in the recordset, and cannot "
                "be canceled.\n\n Are you sure you want to do this?"
            )

        if ui.areYouSure(message, defaultNo=True):
            try:
                bizobj.deleteAll()
                # Notify listeners that the row number changed:
                self.raiseEvent(events.RowNumChanged)
            except exceptions.ConnectionLostException as e:
                msg = self._connectionLostMsg(ustr(e))
                self.notifyUser(msg, title=_("Data Connection Lost"), severe=True, exception=e)
                sys.exit()
            except exceptions.dException as e:
                dabo_module.error(_("Delete All failed with response: %s") % e)
                self.notifyUser(ustr(e), title=_("Deletion Not Allowed"), severe=True, exception=e)
        self.update()
        self.afterDeleteAll()
        self.refresh()

    def new(self, dataSource=None):
        """Ask the bizobj to add a new record to the recordset."""
        self.dataSourceParameter = dataSource
        bizobj = self.getBizobj(dataSource)
        if bizobj is None:
            # Running in preview or some other non-live mode
            return
        self.activeControlValid()

        err = self.beforeNew()
        if err:
            self.notifyUser(err)
            return

        try:
            bizobj.new()
        except exceptions.dException as e:
            self.notifyUser(
                _("Add new record failed with response:\n\n%s") % e,
                severe=True,
                exception=e,
            )

        statusText = self.getCurrentRecordText(dataSource)
        self.updateStatusText(statusText)

        # Notify listeners that the row number changed:
        self.update()
        self.raiseEvent(events.RowNumChanged)
        self.afterNew()
        self.refresh()

    def getSQL(self, dataSource=None):
        """Get the current SQL from the bizobj."""
        return self.getBizobj(dataSource).getSQL()

    def setSQL(self, sql, dataSource=None):
        """Set the SQL for the bizobj."""
        self.getBizobj(dataSource).setSQL(sql)

    def _connectionLostMsg(self, err):
        return (
            _(
                """The connection to the database has closed for unknown reasons.
Any unsaved changes to the data will be lost.

Database error message: %s"""
            )
            % err
        )

    def getBizobj(self, dataSource=None, parentBizobj=None):
        """
        Return the bizobj with the passed dataSource. If no
        dataSource is passed, getBizobj() will return the primary bizobj.
        """
        if not parentBizobj and not dataSource:
            return self.PrimaryBizobj

        try:
            if not parentBizobj and dataSource in self.bizobjs:
                return self.bizobjs[dataSource]
        except TypeError:
            # dataSource is not hashable
            pass

        if isinstance(dataSource, biz.dBizobj):
            return dataSource

        if isinstance(dataSource, str) and dataSource.lower() == "form":
            # The form isn't using bizobjs, but locally-bound data
            # controls
            return self

        # See if it is the RegID of a registered control
        try:
            reg = self.getObjectByRegID(dataSource)
        except TypeError:
            # dataSource is not hashable
            reg = None
        if reg:
            return reg

        # No top-level bizobj had the dataSource name, so now go through
        # the children, and return the first one that matches.
        if not parentBizobj:
            # start the recursive walk:
            for key in self.bizobjs:
                bo = self.getBizobj(dataSource, self.bizobjs[key])
                if bo:
                    return bo
            # If we got here, none were found:
            return None
        else:
            # called by the walk block above
            for child in parentBizobj.getChildren():
                if child.DataSource == dataSource:
                    return child
                else:
                    bo = self.getBizobj(dataSource, child)
                    if bo:
                        return bo
            # if we got here, none were found
            return None

    def onFirst(self, evt):
        self.first()

    def onPrior(self, evt):
        self.prior()

    def onNext(self, evt):
        next(self)

    def onLast(self, evt):
        self.last()

    def onSave(self, evt):
        self.save()

    def onCancel(self, evt):
        self.cancel()

    def onNew(self, evt):
        self.new()

    def onDelete(self, evt):
        self.delete()

    # Define all of the hook methods
    def beforeFirst(self):
        pass

    def beforeLast(self):
        pass

    def beforePrior(self):
        pass

    def beforeNext(self):
        pass

    def beforeFilter(self):
        pass

    def beforeSave(self):
        pass

    def beforeCancel(self):
        pass

    def beforeRequery(self):
        pass

    def beforeDelete(self):
        pass

    def beforeDeleteAll(self):
        pass

    def beforeNew(self):
        pass

    def beforePointerMove(self):
        pass

    def afterFirst(self):
        pass

    def afterLast(self):
        pass

    def afterPrior(self):
        pass

    def afterNext(self):
        pass

    def afterFilter(self):
        pass

    def afterSave(self):
        pass

    def afterCancel(self):
        pass

    def afterRequery(self):
        pass

    def afterDelete(self):
        pass

    def afterDeleteAll(self):
        pass

    def afterNew(self):
        pass

    def afterPointerMove(self):
        """
        Called after the PrimaryBizobj's RowNumber has changed,
        and the form has been updated.
        """
        pass

    def afterRowNavigation(self):
        """
        Called after the PrimaryBizobj's RowNumber has changed,
        but before the form updates.
        """
        pass

    def getCurrentRecordText(self, dataSource=None, grid=None):
        """Get the text to describe which record is current."""
        self.dataSourceParameter = dataSource
        if dataSource is None and grid is not None:
            # This is being called by a regular grid not tied to a bizobj
            rowCount = grid.RowCount
            rowNumber = grid.CurrentRow + 1
        else:
            bizobj = self.getBizobj(dataSource)
            if bizobj is None:
                try:
                    # Some situations, such as form preview mode, will
                    # store these directly, since they lack bizobjs
                    rowCount = self.rowCount
                    rowNumber = self.rowNumber + 1
                except AttributeError:
                    return ""
            else:
                rowCount = bizobj.RowCount
                if rowCount > 0:
                    rowNumber = bizobj.RowNumber + 1
                else:
                    rowNumber = 1
        if rowCount < 1:
            return _("No records")
        return _("Record %(rowNumber)s/%(rowCount)s") % locals()

    def validateField(self, ctrl):
        """
        Call the bizobj for the control's DataSource. If the control's
        value is rejected for field validation reasons, a
        BusinessRuleViolation exception will be raised, and the form
        can then respond to this.
        """
        if self._fieldValidationControl:
            # Prevent infinite loops
            return
        ds = ctrl.DataSource
        df = ctrl.DataField
        val = ctrl.Value
        if not ds or not df:
            # DataSource/Field is missing; nothing to validate.
            return True
        bizobj = self.getBizobj(ds)
        if not bizobj:
            # Now that DataSources are not always bizobjs, just return
            ## No bizobj for that DataSource; record the error
            # dabo_module.error("No business object found for DataSource: '%s', DataField: '%s' "
            #        % (ds, df))
            return True
        if not isinstance(bizobj, biz.dBizobj):
            # DataSource isn't a bizobj, so no need to validate
            return True
        ret = False
        try:
            bizobj.fieldValidation(df, val)
            ret = True
        except exceptions.BusinessRuleViolation as e:
            self.onFieldValidationFailed(ctrl, ds, df, val, e)
        except exceptions.BusinessRulePassed:
            self.onFieldValidationPassed(ctrl, ds, df, val)
            ret = True
        return ret

    def onFieldValidationFailed(self, ctrl, ds, df, val, err):
        """
        Basic handling of field-level validation failure. You should
        override it with your own code to handle this failure
        appropriately for your application.
        """
        self.StatusText = _("Validation failed for %(df)s: %(err)s") % locals()
        ui.callAfter(ctrl.setFocus)
        self._fieldValidationControl = ctrl

    def onFieldValidationPassed(self, ctrl, ds, df, val):
        """
        Basic handling when field-level validation succeeds.
        You should override it with your own code to handle this event
        appropriately for your application.
        """
        pass

    # Property definitions
    @property
    def CancelChildren(self):
        """Specifies whether changes are canceled from child bizobjs. (bool; default:True)"""
        try:
            return self._CancelChildren
        except AttributeError:
            return True

    @CancelChildren.setter
    def CancelChildren(self, value):
        self._CancelChildren = bool(value)

    @property
    def CheckForChanges(self):
        """
        Specifies whether the user is prompted to save or discard changes. (bool)

        If True (the default), when operations such as requery() or the closing of the form are
        about to occur, the user will be presented with a dialog box asking whether to save changes,
        discard changes, or cancel the operation that led to the dialog being presented.
        """
        return self._checkForChanges

    @CheckForChanges.setter
    def CheckForChanges(self, value):
        self._checkForChanges = bool(value)

    @property
    def DataUpdateDelay(self):
        """
        Specifies synchronization delay in data updates from business to UI layer. (int; default:100
        [ms])

        Set to 0 or None to ensure controls reflect immediately to the data changes.
        """
        return self._dataUpdateDelay

    @DataUpdateDelay.setter
    def DataUpdateDelay(self, val):
        self._dataUpdateDelay = val

    @property
    def PrimaryBizobj(self):
        """
        Reference to the primary bizobj for this form  (dBizobj)

        The attribute '_primaryBizobj' should be a bizobj, but due
        to old code design, might be a data source name. These methods
        will handle the old style, but work primarily with the preferred
        new style.
        """
        bo = None
        if isinstance(self._primaryBizobj, biz.dBizobj):
            bo = self._primaryBizobj
        else:
            if self._primaryBizobj in self.bizobjs:
                bo = self.bizobjs[self._primaryBizobj]
                # Update to bizobj reference
                self._primaryBizobj = bo
        return bo

    @PrimaryBizobj.setter
    def PrimaryBizobj(self, bizOrDataSource):
        if isinstance(bizOrDataSource, biz.dBizobj):
            self._primaryBizobj = bizOrDataSource
        else:
            try:
                bo = self.bizobjs[bizOrDataSource]
            except KeyError:
                bo = None
            if bo:
                self._primaryBizobj = bo
                self.afterSetPrimaryBizobj()
            else:
                dabo_module.info(_("bizobj for data source %s does not exist.") % bizOrDataSource)

    @property
    def RequeryOnLoad(self):
        """Specifies whether an automatic requery happens when the form is loaded.  (bool)"""
        try:
            return self._requeryOnLoad
        except AttributeError:
            return False

    @RequeryOnLoad.setter
    def RequeryOnLoad(self, value):
        self._requeryOnLoad = bool(value)

    @property
    def RowNavigationDelay(self):
        """
        Specifies optional delay to wait for updating the entire form when the user is navigating
        the records. (int; default=0 [ms])

        Set to 0 or None to ensure that all controls reflect immediately to the data changes.
        Setting to a positive non-zero value will result in the following behavior:

        As the row number changes, events.RowNavigation events will fire and the
        afterRowNavigation() hook method will be called, allowing your form code to update a
        specific set of controls so the user knows the records are being navigated. The default
        behavior will reflect the current row number in the form's status bar as row navigation is
        occurring.

        After a navigation and the RowNavigationDelay has passed, the form will be completely
        updated and refreshed. events.RowNumChanged will be fired, and the hook afterPointerMove()
        will be called.

        Recommended setting if non-zero: 250 [ms]. Values under that result in the timer firing
        before the user can navigate again, although this will be dependent on your specific
        situation.
        """
        return self._rowNavigationDelay

    @RowNavigationDelay.setter
    def RowNavigationDelay(self, val):
        self._rowNavigationDelay = val

    @property
    def SaveAllRows(self):
        """Specifies whether changes are saved to all rows, or just the current row. (bool)"""
        try:
            return self._SaveAllRows
        except AttributeError:
            return True

    @SaveAllRows.setter
    def SaveAllRows(self, value):
        self._SaveAllRows = bool(value)

    @property
    def SaveChildren(self):
        """Specifies whether changes are saved to child bizobjs. (bool; default:True)"""
        try:
            return self._SaveChildren
        except AttributeError:
            return True

    @SaveChildren.setter
    def SaveChildren(self, value):
        self._SaveChildren = bool(value)


class dForm(BaseForm, wx.Frame):
    def __init__(self, parent=None, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dForm
        self._mdi = False

        if kwargs.pop("Modal", False):
            # Hack this into a wx.Dialog, for true modality
            dForm._hackToDialog()
            preClass = wx.Dialog
            self._modal = True
        else:
            # Normal dForm
            if settings.MDI and isinstance(parent, wx.MDIParentFrame):
                # Hack this into an MDI Child:
                preClass = wx.MDIChildFrame
                self._mdi = True
            else:
                # This is a normal SDI form:
                preClass = wx.Frame
                self._mdi = False
            dForm._hackToFrame()

        ## (Note that it is necessary to run the above blocks each time, because
        ##  we are modifying the dForm class definition globally.)
        BaseForm.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )
        dForm._hackToFrame()

    def _hackToDialog(cls):
        dForm.__bases__ = (BaseForm, wx.Dialog)

    _hackToDialog = classmethod(_hackToDialog)

    def _hackToFrame(cls):
        if settings.MDI:
            dForm.__bases__ = (BaseForm, wx.MDIChildFrame)
        else:
            dForm.__bases__ = (BaseForm, wx.Frame)

    _hackToFrame = classmethod(_hackToFrame)

    def Show(self, show=True):
        if self.Modal:
            dForm._hackToDialog()
        # dForm.__bases__[-1].Show(self, show)
        ret = super().Show(show)
        dForm._hackToFrame()
        return ret

    # Property definitions
    @property
    def Modal(self):
        """
        Specifies whether this dForm is modal or not  (bool)

        A modal dForm runs its own event loop, blocking program flow until the form is hidden or
        closed, exactly like a dDialog does it. This property may only be sent to the constructor,
        and once instantiated you may not change the modality of a form. For example::

                frm = dForm(Modal=True)

        will create a modal form.

        .. note::

            That a modal dForm is actually a dDialog, and as such does not have the ability to
            contain MenuBars, StatusBars, or ToolBars.

        """
        return getattr(self, "_modal", False)

    @property
    def Visible(self):
        """Specifies whether the form is shown or hidden.  (bool)"""
        return self.IsShown()

    @Visible.setter
    def Visible(self, val):
        if self._constructed():
            val = bool(val)
            if val and self.Modal:
                dForm._hackToDialog()
                self.ShowModal()
                dForm._hackToFrame()
            else:
                self.Show(val)
        else:
            self._properties["Visible"] = val


class dToolForm(BaseForm, wx.MiniFrame):
    def __init__(self, parent=None, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dToolForm
        preClass = wx.MiniFrame
        self._mdi = False
        style = kwargs.get("style", 0)
        kwargs["style"] = (
            style | wx.RESIZE_BORDER | wx.CAPTION | wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.CLOSE_BOX
        )
        kwargs["TinyTitleBar"] = True
        kwargs["ShowStatusBar"] = False
        kwargs["ShowToolBar"] = False
        BaseForm.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )


class dBorderlessForm(BaseForm, wx.Frame):
    def __init__(self, parent=None, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dBorderlessForm
        style = kwargs.get("style", 0)
        kwargs["style"] = style | wx.NO_BORDER
        kwargs["ShowStatusBar"] = False
        kwargs["ShowSystemMenu"] = False
        kwargs["MenuBarClass"] = None
        preClass = wx.Frame
        BaseForm.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )


ui.BaseForm = BaseForm
ui.dForm = dForm
ui.dToolForm = dToolForm
ui.dBorderlessForm = dBorderlessForm


class _dForm_test(dForm):
    def afterInit(self):
        self.Caption = _("Regular Form")

    def onActivate(self, evt):
        print(_("Activate"))

    def onDeactivate(self, evt):
        print(_("Deactivate"))


class _dBorderlessForm_test(dBorderlessForm):
    def afterInit(self):
        self.btn = dButton(self, Caption=_("Close Borderless Form"))
        self.Sizer.append(self.btn, halign="Center", valign="middle")
        self.layout()
        self.btn.bindEvent(events.Hit, self.close)
        ui.callAfter(self.setSize)

    def setSize(self):
        self.Width, self.Height = self.btn.Width + 60, self.btn.Height + 60
        self.layout()
        self.Centered = True


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_dForm_test)
    test.Test().runTest(_dBorderlessForm_test)
