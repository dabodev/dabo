import wx, dabo
import dabo.dEvents as dEvents
import dFormMixin as fm
import dabo.dException as dException
import dabo.dConstants as k
import dProgressDialog
import dSizer
from dabo.dLocalize import _
import time
import sys


class dFormBase(fm.dFormMixin):
	""" Create a dForm object, which is a bizobj-aware form.

	dForm knows how to handle one or more dBizobjs, providing proxy methods 
	like next(), last(), save(), and requery().
	"""

	def __init__(self, preClass, parent, properties, *args, **kwargs):
		self.bizobjs = {}
		self._primaryBizobj = None
		
		# If this is True, a panel will be automatically added to the
		# form and sized to fill the form.
		self.mainPanel = None
		self.mkPanel = self._extractKey(kwargs, "panel")
		
		# Use this for timing queries and other long-
		# running events
		self.stopWatch = wx.StopWatch()
		self.stopWatch.Pause()

		# Determines if the user is prompted to save changes
		# when the form is closed.
		self.checkForChanges = True
		
		fm.dFormMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

# 		if self.mainPanel:
# 			# Can't do this in the _afterInit, as properties haven't been
# 			# applied at that point.
# 			self.mainPanel.BackColor = self.BackColor
		
		
		# Used to override some cases where the status
		# text should be displayed despite other processes
		# trying to overwrite it
		self._holdStatusText = ""


		
	def _afterInit(self):
		self.Sizer = dSizer.dSizer("vertical")
		self.Sizer.layout()
		if self.mkPanel:
			mp = self.mainPanel = dabo.ui.dPanel(self)
			self.Sizer.append(mp, 1, "x")
			mp.Sizer = dabo.ui.dSizer(self.Sizer.Orientation)
		super(dFormBase, self)._afterInit()
	
	
	def show(self):
		self.Visible = True
		
		
	def showModal(self):
		self.MakeModal(True)
		self.Visible = True
		
		
	def hide(self):
		self.Visible = False
		

	def _beforeClose(self, evt=None):
		""" See if there are any pending changes in the form, if the
		form is set for checking for this. If everything's OK, call the 
		hook method.
		"""
		ret = True
		if not self._isClosed:
			self.activeControlValid()
			ret = self.confirmChanges()
		if ret:
			ret = super(dFormBase, self)._beforeClose(evt)
		return ret
		
		
	def confirmChanges(self):
		""" If the form's checkForChanges property is true,
		see if there are any pending changes on the form's bizobjs.
		If so, ask the user if they want to save/discard/cancel.
		
		Subclasses may have their own bizobj management schemes,
		so we can't rely on simplyreferring to PrimaryBizobj here.
		Instead, we'll call a special method that will return a list
		of bizobjs to act upon.
		"""
		if not self.checkForChanges:
			# Don't bother checking
			return True
		bizList = self.getBizobjsToCheck()
		
		if bizList:
			changed = False
			for biz in bizList:
				if biz:
					# Forms can return None in the list, so skip those
					changed = changed or biz.isAnyChanged()
			
			if changed:
				response = dabo.ui.areYouSure(_("Do you wish to save your changes?"),
						cancelButton=True)
				if response == None:    # cancel
					# They canceled, so don't let the form close
					return False
				elif response == True:  # yes
					for biz in bizList:
						self.save(dataSource=biz.DataSource)
		return True
	
	
	def getBizobjsToCheck(self):
		""" Default behavior is to simply check the primary bizobj.
		However, there may be cases in subclasses where a different
		bizobj may be checked, or even several. In those cases, override
		this method and return a list of the required bizobjs.
		"""
		return [self.PrimaryBizobj]
		
		
	def addBizobj(self, bizobj):
		""" Add a bizobj to this form.

		Make the bizobj the form's primary bizobj if it is the first bizobj to 
		be added.
		"""
		self.bizobjs[bizobj.DataSource] = bizobj
		if len(self.bizobjs) == 1:
			self.PrimaryBizobj = bizobj
		self.setStatusText("Bizobj '%s' %s." % (bizobj.DataSource, _("added")))


	def afterSetPrimaryBizobj(self):
		""" Subclass hook."""
		pass


	def moveToRowNumber(self, rowNumber, dataSource=None):
		""" Move the record pointer to the specified row."""
		bizobj = self.getBizobj(dataSource)
		if bizobj is None:
			# Running in preview or some other non-live mode
			return
		self._moveRecordPointer(bizobj.moveToRowNumber, dataSource, rowNumber)


	def _moveRecordPointer(self, func, dataSource=None, *args, **kwargs):
		""" Move the record pointer using the specified function."""
		
		biz = self.getBizobj(dataSource)
		oldRowNum = biz.RowNumber

		self.activeControlValid()
		err = self.beforePointerMove()
		if err:
			self.notifyUser(err)
			return
		try:
			response = func(*args, **kwargs)
		except dException.NoRecordsException:
			self.setStatusText(_("No records in dataset."))
		except dException.BeginningOfFileException:
			self.setStatusText(self.getCurrentRecordText(dataSource) + " (BOF)")
		except dException.EndOfFileException:
			self.setStatusText(self.getCurrentRecordText(dataSource) + " (EOF)")
		except dException.dException, e:
			self.notifyUser(str(e))
		else:
			if biz.RowNumber != oldRowNum:
				# Notify listeners that the row number changed:
				dabo.ui.callAfter(self.raiseEvent, dEvents.RowNumChanged)
			self.refreshControls()
		self.afterPointerMove()


	def first(self, dataSource=None):
		""" Ask the bizobj to move to the first record."""
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
		""" Ask the bizobj to move to the last record."""
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
		""" Ask the bizobj to move to the previous record."""
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
		""" Ask the bizobj to move to the next record."""
		bizobj = self.getBizobj(dataSource)
		if bizobj is None:
			# Running in preview or some other non-live mode
			return
		err = self.beforeNext()
		if err:
			self.notifyUser(err)
			return
		self._moveRecordPointer(bizobj.next, dataSource)
		self.afterNext()
		

	def save(self, dataSource=None):
		""" Ask the bizobj to commit its changes to the backend."""
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
				bizobj.saveAll()
			else:
				bizobj.save()
				
			self.setStatusText(_("Changes to %s saved.") % (
					self.SaveAllRows and "all records" or "current record",))
					
		except dException.ConnectionLostException, e:
			msg = self._connectionLostMsg(str(e))
			self.notifyUser(msg, title=_("Data Connection Lost"), severe=True)
			sys.exit()

		except dException.NoRecordsException, e:
			# No records were saved. No big deal; just let 'em know.
			self.setStatusText(_("Nothing to save!"))
			return True
			
		except dException.BusinessRuleViolation, e:
			self.setStatusText(_("Save failed."))
			msg = "%s:\n\n%s" % (_("Save Failed"), _( str(e) ))
			self.notifyUser(msg, severe=True)
			return False

		self.afterSave()
		return True
	
	
	def cancel(self, dataSource=None):
		""" Ask the bizobj to cancel its changes.

		This will revert back to the state of the records when they were last
		requeried or saved.
		"""
		bizobj = self.getBizobj(dataSource)
		if bizobj is None:
			# Running in preview or some other non-live mode
			return
		self.activeControlValid()

		err = self.beforeCancel()
		if err:
			self.notifyUser(err)
			return
		try:
			if self.SaveAllRows:
				bizobj.cancelAll()
			else:
				bizobj.cancel()
			self.setStatusText(_("Changes to %s canceled.") % (
					self.SaveAllRows and "all records" or "current record",))
			self.refreshControls()
		except dException.dException, e:
			dabo.errorLog.write(_("Cancel failed with response: %s") % str(e))
			self.notifyUser(str(e), title=_("Cancel Not Allowed") )
		self.afterCancel()


	def onRequery(self, evt):
		""" Occurs when an EVT_MENU event is received by this form."""
		self.requery()
		self.Raise()
		evt.Skip()


	def requery(self, dataSource=None):
		""" Ask the bizobj to requery."""
		ret = False
		bizobj = self.getBizobj(dataSource)
		if bizobj is None:
			# Running in preview or some other non-live mode
			return
		self.activeControlValid()

		err = self.beforeRequery()
		if err:
			self.notifyUser(err)
			return
		if bizobj.isAnyChanged() and self.AskToSave:
			response = dabo.ui.areYouSure(_("Do you wish to save your changes?"),
								cancelButton=True)

			if response == None:    # cancel
				return
			elif response == True:  # yes
				if not self.save(dataSource=dataSource):
					# The save failed, so don't continue with the requery
					return

		self.setStatusText(_("Please wait... requerying dataset..."))
		
		try:
			self.stopWatch.Start()
			response = dProgressDialog.displayAfterWait(self, 2, bizobj.requery)
#			response = bizobj.requery()
			self.stopWatch.Pause()
			elapsed = round(self.stopWatch.Time()/1000.0, 3)
			
			self.refreshControls()

			# Notify listeners that the row number changed:
			self.raiseEvent(dEvents.RowNumChanged)
			
			# We made it through without errors
			ret = True
		
			self._holdStatusText = (
					_("%s record%sselected in %s second%s") % (
					bizobj.RowCount, 
					bizobj.RowCount == 1 and " " or "s ",
					elapsed,
					elapsed == 1 and "." or "s."))

		except dException.MissingPKException, e:
			self.notifyUser(str(e), title=_("Requery Failed"), severe=True)

		except dException.ConnectionLostException, e:
			msg = self._connectionLostMsg(str(e))
			self.notifyUser(msg, title=_("Data Connection Lost"), severe=True)
			sys.exit()

		except dException.dException, e:
			dabo.errorLog.write(_("Requery failed with response: %s") % str(e))
			self.notifyUser(str(e), title=_("Requery Not Allowed"), severe=True)
		self.afterRequery()
		return ret
		

	def delete(self, dataSource=None, message=None):
		""" Ask the bizobj to delete the current record."""
		bizobj = self.getBizobj(dataSource)
		if bizobj is None:
			# Running in preview or some other non-live mode
			return

		ds = bizobj.DataSource

		self.activeControlValid()
		
		if not bizobj.RowCount > 0:
			# Nothing to delete!
			self.setStatusText(_("Nothing to delete!"))
			return
			
		err = self.beforeDelete()
		if err:
			self.notifyUser(err)
			return
		if message is None:
			message = _("This will delete the current record from %s, and cannot "
					"be canceled.\n\n Are you sure you want to do this?") % ds
		if dabo.ui.areYouSure(message, defaultNo=True):
			try:
				bizobj.delete()
				self.setStatusText(_("Record Deleted."))
				self.refreshControls()
				# Notify listeners that the row number changed:
				self.raiseEvent(dEvents.RowNumChanged)
			except dException.ConnectionLostException, e:
				msg = self._connectionLostMsg(str(e))
				self.notifyUser(msg, title=_("Data Connection Lost"), severe=True)
				sys.exit()
			except dException.dException, e:
				dabo.errorLog.write(_("Delete failed with response: %s") % str(e))
				self.notifyUser(str(e), title=_("Deletion Not Allowed"), severe=True)
		self.afterDelete()
		

	def deleteAll(self, dataSource=None, message=None):
		""" Ask the primary bizobj to delete all records from the recordset."""
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
			message = _("This will delete all records in the recordset, and cannot "
						"be canceled.\n\n Are you sure you want to do this?")

		if dabo.ui.areYouSure(message, defaultNo=True):
			try:
				bizobj.deleteAll()
				self.refreshControls()
				# Notify listeners that the row number changed:
				self.raiseEvent(dEvents.RowNumChanged)
			except dException.ConnectionLostException, e:
				msg = self._connectionLostMsg(str(e))
				self.notifyUser(msg, title=_("Data Connection Lost"), severe=True)
				sys.exit()
			except dException.dException, e:
				dabo.errorLog.write(_("Delete All failed with response: %s") % str(e))
				self.notifyUser(str(e), title=_("Deletion Not Allowed"), severe=True)
		self.afterDeleteAll()
		

	def new(self, dataSource=None):
		""" Ask the bizobj to add a new record to the recordset."""
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
		except dException.dException, e:
			self.notifyUser(_("Add new record failed with response:\n\n%s" % str(e)), 
					severe=True)

		statusText = self.getCurrentRecordText(dataSource)
		self.setStatusText(statusText)
		self.refreshControls()

		# Notify listeners that the row number changed:
		self.raiseEvent(dEvents.RowNumChanged)

		self.afterNew()
		

	def afterNew(self): pass


	def getSQL(self, dataSource=None):
		""" Get the current SQL from the bizobj."""
		return self.getBizobj(dataSource).getSQL()


	def setSQL(self, sql, dataSource=None):
		""" Set the SQL for the bizobj."""
		self.getBizobj(dataSource).setSQL(sql)
		
	
	def notifyUser(self, msg, title="Notice", severe=False):
		""" Displays an alert messagebox for the user. You can customize
		this in your own classes if you prefer a different display.
		"""
		if severe:
			func = dabo.ui.stop
		else:
			func = dabo.ui.info
		func(message=msg, title=title)


	def _connectionLostMsg(self, err):
		return _("""The connection to the database has closed for unknown reasons.
Any unsaved changes to the data will be lost.

Database error message: %s""") %	err


	def getBizobj(self, dataSource=None, parentBizobj=None):
		""" Return the bizobj with the passed dataSource. If no 
		dataSource is passed, getBizobj() will return the primary bizobj.
		"""
		if not parentBizobj and not dataSource:
			return self.PrimaryBizobj
		
		if not parentBizobj and self.bizobjs.has_key(dataSource):
			return self.bizobjs[dataSource]
			
		if dataSource.lower() == "form":
			# The form isn't using bizobjs, but locally-bound data
			# controls
			return self
		
		# See if it is the RegID of a registered control
		reg = self.getObjectByRegID(dataSource)
		if reg:
			return reg

		# No top-level bizobj had the dataSource name, so now go through
		# the children, and return the first one that matches.
		if not parentBizobj:
			# start the recursive walk:
			for key in self.bizobjs.keys():
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
			

	def onFirst(self, evt): self.first()
	def onPrior(self, evt): self.prior()
	def onNext(self, evt): self.next()
	def onLast(self, evt): self.last()
	def onSave(self, evt): self.save()
	def onCancel(self, evt): self.cancel()
	def onNew(self, evt): self.new()
	def onDelete(self, evt): self.delete()

	# Define all of the hook methods
	def beforeFirst(self): pass
	def beforeLast(self): pass
	def beforePrior(self): pass
	def beforeNext(self): pass
	def beforeSave(self): pass
	def beforeCancel(self): pass
	def beforeRequery(self): pass
	def beforeDelete(self): pass
	def beforeDeleteAll(self): pass
	def beforeNew(self): pass
	def beforePointerMove(self): pass
	def afterFirst(self): pass
	def afterLast(self): pass
	def afterPrior(self): pass
	def afterNext(self): pass
	def afterSave(self): pass
	def afterCancel(self): pass
	def afterRequery(self): pass
	def afterDelete(self): pass
	def afterDeleteAll(self): pass
	def afterNew(self): pass
	def afterPointerMove(self): pass


	def getCurrentRecordText(self, dataSource=None, grid=None):
		""" Get the text to describe which record is current.
		"""
		if dataSource is None and grid is not None:
			# This is being called by a regular grid not tied to a bizobj
			rowCount = grid.RowCount
			rowNumber = grid.CurrentRow+1
		else:
			bizobj = self.getBizobj(dataSource)
			if bizobj is None:
				try:
					# Some situations, such as form preview mode, will
					# store these directly, since they lack bizobjs
					rowCount = self.rowCount
					rowNumber = self.rowNumber+1
				except:
					rowCount = 1
					rowNumber = 1
			else:
				rowCount = bizobj.RowCount
				if rowCount > 0:
					rowNumber = bizobj.RowNumber+1
				else:
					rowNumber = 1
		return _("Record %s/%s" % (rowNumber, rowCount))


	def activeControlValid(self):
		""" Force the control-with-focus to fire its KillFocus code.

		The bizobj will only get its field updated during the control's 
		KillFocus code. This function effectively commands that update to
		happen before it would have otherwise occurred.
		"""
		ac = self.ActiveControl
		if ac is not None:
			try:
				ac.flushValue()
			except AttributeError:
				# active control may not be data-aware
				pass
				
	
	def validateField(self, ctrl):
		"""Call the bizobj for the control's DataSource. If the control's 
		value is rejected for field validation reasons, a 
		BusinessRuleViolation exception will be raised, and the form
		can then respond to this.
		"""
		
		ds = ctrl.DataSource
		df = ctrl.DataField
		val = ctrl.Value
		if not ds or not df:
			# DataSource/Field is missing; nothing to validate.
			return
		biz = self.getBizobj(ds)
		if not biz:
			# No bizobj for that DataSource; record the error
			dabo.errorLog.write("No business object found for DataSource: '%s', DataField: '%s' "
					% (ds, df))
			return
		if not isinstance(biz, dabo.biz.dBizobj):
			# DataSource isn't a bizobj, so no need to validate
			return True
		ret = False
		try:
			biz.fieldValidation(df, val)
			ret = True
		except dException.BusinessRuleViolation, e:
			self.onFieldValidationFailed(ctrl, ds, df, val, e)
		return ret


	def onFieldValidationFailed(self, ctrl, ds, df, val, err):
		"""Basic handling of field-level validation failure. You should
		override it with your own code to handle this failure 
		appropriately for your application.
		"""
		self.setStatusText(_("Validation failed for %s: %s") % (df, err))
		dabo.ui.callAfter(ctrl.setFocus)
		
	
	# Property get/set/del functions follow.
	def _getAskToSave(self):
		try:
			return self._AskToSave
		except AttributeError:
			return True
	def _setAskToSave(self, value):
		self._AskToSave = bool(value)

	def _getSaveAllRows(self):
		try:
			return self._SaveAllRows
		except AttributeError:
			return True
	def _setSaveAllRows(self, value):
		self._SaveAllRows = bool(value)

	def _getPrimaryBizobj(self):
		"""The attribute '_primaryBizobj' should be a bizobj, but due
		to old code design, might be a data source name. These methods
		will handle the old style, but work primarily with the preferred
		new style.
		"""
		bo = None
		if isinstance(self._primaryBizobj, dabo.biz.dBizobj):
			bo = self._primaryBizobj
		else:
			if self.bizobjs.has_key(self._primaryBizobj):
				bo = self.bizobjs[self._primaryBizobj]
				# Update to bizobj reference
				self._primaryBizobj = bo
		return bo
	def _setPrimaryBizobj(self, bizOrDataSource):
		if isinstance(bizOrDataSource, dabo.biz.dBizobj):
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
				dabo.infoLog.write(_("bizobj for data source %s does not exist.") % bizOrDataSource)



	# Property definitions:
	AskToSave = property(_getAskToSave, _setAskToSave, None, 
			_("""Specifies whether a save prompt appears before the data
			is requeried. (bool)""") )

	PrimaryBizobj = property(_getPrimaryBizobj, _setPrimaryBizobj, None, 
			_("Reference to the primary bizobj for this form  (dBizobj)") )

	SaveAllRows = property(_getSaveAllRows, _setSaveAllRows, None, 
			_("Specifies whether dataset is row- or table-buffered. (bool)") )


class dFormSDI(wx.Frame, dFormBase):
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dForm
		preClass = wx.PreFrame
		self._mdi = False
		dFormBase.__init__(self, preClass, parent, properties, *args, **kwargs)


class dFormParentMDI(wx.MDIParentFrame, dFormBase):
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dForm
		preClass = wx.PreMDIParentFrame
		self._mdi = True
		dFormBase.__init__(self, preClass, parent, properties, *args, **kwargs)


class dFormChildMDI(wx.MDIChildFrame, dFormBase):
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dForm
		preClass = wx.PreMDIChildFrame
		self._mdi = True
		dFormBase.__init__(self, preClass, parent, properties, *args, **kwargs)


if dabo.settings.MDI:
	dForm = dFormChildMDI
else:
	dForm = dFormSDI


class dToolForm(dFormSDI):
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		style = self._extractKey(kwargs, "style", 0)
		style = style | wx.FRAME_TOOL_WINDOW | wx.STAY_ON_TOP | wx.RESIZE_BORDER
		kwargs["style"] = style	
		kwargs["ShowStatusBar"] = False
		kwargs["ShowToolBar"] = False
		self.MenuBarClass = None
# 		kwargs[""] = 
		super(dToolForm, self).__init__(parent=parent, properties=properties, *args, **kwargs)

			
					
if __name__ == "__main__":
	import test
	test.Test().runTest(dForm)
