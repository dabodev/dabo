import wx, dabo
import dabo.dEvents as dEvents
import dFormMixin as fm
import dabo.dException as dException
import dabo.dConstants as k
import dMessageBox, dProgressDialog
import dSizer
from dabo.dLocalize import _
import time

# Different platforms expect different frame types. Notably,
# most users on Windows expect and prefer the MDI parent/child
# type frames.

# pkm 06/09/2004: disabled MDI even on Windows. There are some issues that I
#                 don't have time to track down right now... better if it works
#                 on Windows similarly to Linux instead of not at all... if you
#                 want to enable MDI on Windows, just take out the "False and"
#                 in the below if statement, and do the same in dFormMain.py.

if False and wx.Platform == '__WXMSW__':
	wxFrameClass = wx.MDIChildFrame
	wxPreFrameClass = wx.PreMDIChildFrame
else:
	wxFrameClass = wx.Frame
	wxPreFrameClass = wx.PreFrame


class dForm(wxFrameClass, fm.dFormMixin):
	""" Create a dForm object, which is a bizobj-aware form.

	dForm knows how to handle one or more dBizobjs, providing proxy methods 
	like next(), last(), save(), and requery().
	"""
	def __init__(self, parent=None, id=-1, title='', name='dForm', *args, **kwargs):
		self._baseClass = dForm
		if parent:
			style = wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT
		else:
			style = wx.DEFAULT_FRAME_STYLE

		pre = wxPreFrameClass()
		self._beforeInit(pre)                  # defined in dPemMixin
		pre.Create(parent, id, title, name=name, style=style|pre.GetWindowStyle(), *args, **kwargs)

		self.PostCreate(pre)
		
		try:		
			self.Name, self.Caption = name, name
		except NameError:
			# Name isn't unique: punt for now: likely, user code will change the
			# name anyway.
			name = "%s_%s" % (name, self.GetId())
			self.Name, self.Caption = name, name
			
		fm.dFormMixin.__init__(self)

		self.debug = False
		self.bizobjs = {}
		self._primaryBizobj = None

		if not isinstance(self, wx.MDIChildFrame):
			self.CreateStatusBar()

		self.Sizer = dSizer.dSizer("vertical")
		self.Sizer.layout()
		
		if self.Application is not None:
			self.Application.uiForms.add(self)
		
		self.bindEvent(dEvents.Close, self.__onClose)
		self.bindEvent(dEvents.Activate, self.__onActivate)
		self.bindEvent(dEvents.Deactivate, self.__onDeactivate)
		
		# Determines if the user is prompted to save changes
		# when the form is closed.
		self.checkForChanges = True

		self._afterInit()                      # defined in dPemMixin


	def confirmChanges(self):
		""" If the form's checkForChanges property is true,
		see if there are any pending changes on the form's bizobjs.
		If so, ask the user if they want to save/discard/cancel.
		
		Subclasses may have their own bizobj management schemes,
		so we can't rely on simply calling getPrimaryBizobj() here.
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
				response = dMessageBox.areYouSure(_("Do you wish to save your changes?"),
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
		return [self.getPrimaryBizobj()]
		
		
	def _beforeClose(self, evt):
		""" See if there are any pending changes in the form, if the
		form is set for checking for this. If everything's OK, call the 
		hook method.
		"""
		ret = self.confirmChanges()
		if ret:
			ret = self.beforeClose(evt)
		return ret
		
		
	def beforeClose(self, evt):
		""" Hook method. Returning False will prevent the form from 
		closing. Gives you a chance to determine the status of the form
		to see if changes need to be saved, etc.
		"""
		return True
		
		
	def close(self):
		""" Stub method to be customized in subclasses. At this point,
		the form is going to close. If you need to do something that might
		prevent the form from closing, code it in the beforeClose() 
		method instead.
		"""
		pass
		

	def addBizobj(self, bizobj):
		""" Add a bizobj to this form.

		Make the bizobj the form's primary bizobj if it is the first bizobj to 
		be added.
		"""
		self.bizobjs[bizobj.DataSource] = bizobj
		if len(self.bizobjs) == 1:
			self.setPrimaryBizobj(bizobj.DataSource)
		if self.debug:
			dabo.infoLog.write(_("Added bizobj with DataSource of %s") % bizobj.DataSource)
		self.setStatusText("Bizobj '%s' %s." % (bizobj.DataSource, _("added")))


	def getPrimaryBizobj(self):
		bo = None
		if self.bizobjs.has_key(self._primaryBizobj):
			bo = self.bizobjs[self._primaryBizobj]
		return bo


	def setPrimaryBizobj(self, dataSource):
		try:
			bo = self.bizobjs[dataSource]
		except KeyError:
			bo = None
		if bo:
			self._primaryBizobj = dataSource
			self.afterSetPrimaryBizobj()
		else:
			dabo.infoLog.write(_("bizobj for data source %s does not exist.") % dataSource)


	def afterSetPrimaryBizobj(self):
		""" Subclass hook.
		"""
		pass


	def refreshControls(self):
		""" Refresh the value of all contained dControls.

		Raises EVT_VALUEREFRESH which will be caught by all dControls, who will
		in turn refresh themselves with the current value of the field in the
		bizobj. 
		"""
		self.raiseEvent(dEvents.ValueRefresh)
		self.setStatusText(self.getCurrentRecordText())


	def _moveRecordPointer(self, func, dataSource=None):
		""" Move the record pointer using the specified function.
		"""
		self.activeControlValid()
		try:
			response = func()
		except dException.NoRecordsException:
			self.setStatusText(_("No records in dataset."))
		else:
			# Notify listeners that the row number changed:
			self.raiseEvent(dEvents.RowNumChanged)
			self.refreshControls()


	def first(self, dataSource=None):
		""" Ask the bizobj to move to the first record.
		"""
		bizobj = self.getBizobj(dataSource)
		if bizobj is None:
			# Running in preview or some other non-live mode
			return
		self._moveRecordPointer(bizobj.first, dataSource)


	def last(self, dataSource=None):
		""" Ask the bizobj to move to the last record.
		"""
		bizobj = self.getBizobj(dataSource)
		if bizobj is None:
			# Running in preview or some other non-live mode
			return
		self._moveRecordPointer(bizobj.last, dataSource)


	def prior(self, dataSource=None):
		""" Ask the bizobj to move to the previous record.
		"""
		bizobj = self.getBizobj(dataSource)
		if bizobj is None:
			# Running in preview or some other non-live mode
			return
		try:
			self._moveRecordPointer(bizobj.prior, dataSource)
		except dException.BeginningOfFileException:
			self.setStatusText(self.getCurrentRecordText(dataSource) + " (BOF)")

	def next(self, dataSource=None):
		""" Ask the bizobj to move to the next record.
		"""
		bizobj = self.getBizobj(dataSource)
		if bizobj is None:
			# Running in preview or some other non-live mode
			return
		try:
			self._moveRecordPointer(bizobj.next, dataSource)
		except dException.EndOfFileException:
			self.setStatusText(self.getCurrentRecordText(dataSource) + " (EOF)")


	def save(self, dataSource=None):
		""" Ask the bizobj to commit its changes to the backend.
		"""
		bizobj = self.getBizobj(dataSource)
		if bizobj is None:
			# Running in preview or some other non-live mode
			return
		self.activeControlValid()

		try:
			if self.SaveAllRows:
				bizobj.saveAll()
			else:
				bizobj.save()
				
			if self.debug:
				dabo.infoLog.write(_("Save successful."))
			self.setStatusText(_("Changes to %s saved.") % (
					self.SaveAllRows and "all records" or "current record",))
					
		except dException.NoRecordsException, e:
			# No records were saved. No big deal; just let 'em know.
			self.setStatusText(_("Nothing to save!"))
			return True
			
		except dException.BusinessRuleViolation, e:
			self.setStatusText(_("Save failed."))
			dMessageBox.stop("%s:\n\n%s" % (_("Save Failed:"), _(str(e))))
			return False

			
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

		try:
			if self.SaveAllRows:
				bizobj.cancelAll()
			else:
				bizobj.cancel()
			if self.debug:
				dabo.infoLog.write(_("Cancel successful."))
			self.setStatusText(_("Changes to %s canceled.") % (
					self.SaveAllRows and "all records" or "current record",))
			self.refreshControls()
		except dException.dException, e:
			if self.debug:
				dabo.errorLog.write(_("Cancel failed with response: %s") % str(e))
			### TODO: What should be done here? Raise an exception?
			###       Prompt the user for a response?


	def onRequery(self, evt):
		""" Occurs when an EVT_MENU event is received by this form.
		"""
		self.requery()
		self.Raise()
		evt.Skip()


	def requery(self, dataSource=None):
		""" Ask the bizobj to requery.
		"""
		ret = False
		bizobj = self.getBizobj(dataSource)
		if bizobj is None:
			# Running in preview or some other non-live mode
			return
		self.activeControlValid()

		if bizobj.isAnyChanged() and self.AskToSave:
			response = dMessageBox.areYouSure(_("Do you wish to save your changes?"),
								cancelButton=True)

			if response == None:    # cancel
				return
			elif response == True:  # yes
				if not self.save(dataSource=dataSource):
					# The save failed, so don't continue with the requery
					return

		self.setStatusText(_("Please wait... requerying dataset..."))
		start = time.time()

		try:
			response = dProgressDialog.displayAfterWait(self, 2, bizobj.requery)
#			response = bizobj.requery()
			
			stop = round(time.time() - start, 3)
			if self.debug:
				dabo.infoLog.write(_("Requery successful."))
			self.setStatusText(_("%s record%sselected in %s second%s") % (
					bizobj.RowCount, 
					bizobj.RowCount == 1 and " " or "s ",
					stop,
					stop == 1 and "." or "s."))
			self.refreshControls()

			# Notify listeners that the row number changed:
			self.raiseEvent(dEvents.RowNumChanged)
			
			# We made it through without errors
			ret = True
		
		except dException.MissingPKException, e:
			dabo.ui.dMessageBox.stop(str(e), "Requery Failed")

		except dException.dException, e:
			dabo.errorLog.write(_("Requery failed with response: %s") % str(e))
			### TODO: What should be done here? Raise an exception?
			###       Prompt the user for a response?
		return ret

	def delete(self, dataSource=None, message=None):
		""" Ask the bizobj to delete the current record.
		"""
		bizobj = self.getBizobj(dataSource)
		if bizobj is None:
			# Running in preview or some other non-live mode
			return
		self.activeControlValid()
		
		if not bizobj.RowCount > 0:
			# Nothing to delete!
			self.setStatusText(_("Nothing to delete!"))
			return
			
		if not message:
			message = _("This will delete the current record, and cannot "
						"be canceled.\n\n Are you sure you want to do this?")
		if dMessageBox.areYouSure(message, defaultNo=True):
			try:
				bizobj.delete()
				if self.debug:
					dabo.infoLog.write(_("Delete successful."))
				self.setStatusText(_("Record Deleted."))
				self.refreshControls()
				# Notify listeners that the row number changed:
				self.raiseEvent(dEvents.RowNumChanged)
			except dException.dException, e:
				dabo.errorLog.write(_("Delete failed with response: %s") % str(e))
				### TODO: What should be done here? Raise an exception?
				###       Prompt the user for a response?


	def deleteAll(self, dataSource=None, message=None):
		""" Ask the primary bizobj to delete all records from the recordset.
		"""
		bizobj = self.getBizobj(dataSource)
		if bizobj is None:
			# Running in preview or some other non-live mode
			return
		self.activeControlValid()

		if not message:
			message = _("This will delete all records in the recordset, and cannot "
						"be canceled.\n\n Are you sure you want to do this?")

		if dMessageBox.areYouSure(message, defaultNo=True):
			try:
				bizobj.deleteAll()
				if self.debug:
					dabo.infoLog.write(_("Delete All successful."))
				self.refreshControls()
				# Notify listeners that the row number changed:
				self.raiseEvent(dEvents.RowNumChanged)
			except dException.dException, e:
				dabo.errorLog.write(_("Delete All failed with response: %s") % str(e))
				### TODO: What should be done here? Raise an exception?
				###       Prompt the user for a response?


	def new(self, dataSource=None):
		""" Ask the bizobj to add a new record to the recordset.
		"""
		bizobj = self.getBizobj(dataSource)
		if bizobj is None:
			# Running in preview or some other non-live mode
			return
		self.activeControlValid()
		try:
			bizobj.new()
			if self.debug:
				dabo.infoLog.write(_("New successful."))
			statusText = self.getCurrentRecordText(dataSource)
			self.setStatusText(statusText)
			self.refreshControls()

			# Notify listeners that the row number changed:
			self.raiseEvent(dEvents.RowNumChanged)
			self.afterNew()

		except dException.dException, e:
			dMessageBox.stop(_("Add new record failed with response:\n\n%s" % str(e)))


	def afterNew(self):
		""" Called after a new record is successfully added to the dataset.

		Override in subclasses for desired behavior.
		"""
		pass


	def getSQL(self, dataSource=None):
		""" Get the current SQL from the bizobj.
		"""
		return self.getBizobj(dataSource).getSQL()


	def setSQL(self, sql, dataSource=None):
		""" Set the SQL for the bizobj.
		"""
		self.getBizobj(dataSource).setSQL(sql)


	def getBizobj(self, dataSource=None, parentBizobj=None):
		""" Return the bizobj with the passed dataSource.

		If no dataSource is passed, getBizobj() will return the primary bizobj.
		"""
		if not parentBizobj and not dataSource:
			return self.getPrimaryBizobj()
		
		if not parentBizobj and self.bizobjs.has_key(dataSource):
			return self.bizobjs[dataSource]

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


	def getCurrentRecordText(self, dataSource=None):
		""" Get the text to describe which record is current.
		"""
		bizobj = self.getBizobj(dataSource)
		if bizobj is None:
			try:
				# Some situations, such as form preview mode, will
				# store these directly, since they lack bizobjs
				rowCount = self.rowCount
				rowNumber = self.rowNumber
			except:
				rowCount = 1
				rowNumber = 0
		else:
			rowCount = bizobj.RowCount
			if rowCount > 0:
				rowNumber = bizobj.RowNumber+1
			else:
				rowNumber = 0
		return _("Record " ) + ("%s/%s" % (rowNumber, rowCount))


	def activeControlValid(self):
		""" Force the control-with-focus to fire its KillFocus code.

		The bizobj will only get its field updated during the control's 
		KillFocus code. This function effectively commands that update to
		happen before it would have otherwise occurred.
		"""
		controlWithFocus = self.FindFocus()
		if controlWithFocus:
			try:
				controlWithFocus.flushValue()
			except AttributeError:
				# controlWithFocus may not be data-aware
				pass
	
	def __onActivate(self, evt):
		if self.Application is not None:
			self.Application.ActiveForm = self
	
	def __onDeactivate(self, evt):
		if self.Application is not None and self.Application.ActiveForm == self:
			self.Application.ActiveForm = None

	def __onClose(self, evt):
		if self._beforeClose(evt):
			self.close()
		else:
			evt.stop()
	

	# Property get/set/del functions follow.
	def _getSaveAllRows(self):
		try:
			return self._SaveAllRows
		except AttributeError:
			return True
	def _setSaveAllRows(self, value):
		self._SaveAllRows = bool(value)

	def _getAskToSave(self):
		try:
			return self._AskToSave
		except AttributeError:
			return True
	def _setAskToSave(self, value):
		self._AskToSave = bool(value)

	# Property definitions:
	SaveAllRows = property(_getSaveAllRows, _setSaveAllRows, None, 
			"Specifies whether dataset is row- or table-buffered. (bool)")

	AskToSave = property(_getAskToSave, _setAskToSave, None, 
			"Specifies whether a save prompt appears before the data is requeried. (bool)")


if __name__ == "__main__":
	import test
	test.Test().runTest(dForm)
