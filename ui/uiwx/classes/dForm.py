import wx, dEvents
import dFormMixin as fm
import dabo.dException as dException
import dabo.dConstants as k
import dMessageBox, dProgressDialog
from dabo.dLocalize import _

# Different platforms expect different frame types. Notably,
# most users on Windows expect and prefer the MDI parent/child
# type frames.
if wx.Platform == '__WXMSW__':
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

		self.dControls = {}

		if not isinstance(self, wx.MDIChildFrame):
			self.CreateStatusBar()

		self.SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.GetSizer().Layout()

		self._afterInit()                      # defined in dPemMixin


	def addBizobj(self, bizobj):
		""" Add a bizobj to this form.

		Make the bizobj the form's primary bizobj if it is the first bizobj to 
		be added.
		"""
		self.bizobjs[bizobj.DataSource] = bizobj
		if len(self.bizobjs) == 1:
			self.setPrimaryBizobj(bizobj.DataSource)
		if self.debug:
			print "added bizobj with DataSource of %s" % bizobj.DataSource
		self.setStatusText("Bizobj '%s' %s." % (bizobj.DataSource, _("added")))


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
		""" Subclass hook.
		"""
		pass


	def addControl(self, control):
		""" Add a control to this form.

		This happens automatically for dControls.
		"""
		EVT_VALUEREFRESH = wx.PyEventBinder(dEvents.EVT_VALUEREFRESH, 0)
		EVT_ROWNUMCHANGED = wx.PyEventBinder(dEvents.EVT_ROWNUMCHANGED, 0)    

		self.dControls[control.GetName()] = control

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
		""" Refresh the value of all contained dControls.

		Raises EVT_VALUEREFRESH which will be caught by all dControls, who will
		in turn refresh themselves with the current value of the field in the
		bizobj. 
		"""
		evt = dEvents.dEvent(dEvents.EVT_VALUEREFRESH, self.GetId())
		self.GetEventHandler().ProcessEvent(evt)
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
			evt = dEvents.dEvent(dEvents.EVT_ROWNUMCHANGED, self.GetId())
			self.GetEventHandler().ProcessEvent(evt)

			self.refreshControls()


	def first(self, dataSource=None):
		""" Ask the bizobj to move to the first record.
		"""
		self._moveRecordPointer(self.getBizobj(dataSource).first, dataSource)


	def last(self, dataSource=None):
		""" Ask the bizobj to move to the last record.
		"""
		self._moveRecordPointer(self.getBizobj(dataSource).last, dataSource)


	def prior(self, dataSource=None):
		""" Ask the bizobj to move to the previous record.
		"""
		try:
			self._moveRecordPointer(self.getBizobj(dataSource).prior, dataSource)
		except dException.BeginningOfFileException:
			self.setStatusText(self.getCurrentRecordText(dataSource) + " (BOF)")

	def next(self, dataSource=None):
		""" Ask the bizobj to move to the next record.
		"""
		try:
			self._moveRecordPointer(self.getBizobj(dataSource).next, dataSource)
		except dException.EndOfFileException:
			self.setStatusText(self.getCurrentRecordText(dataSource) + " (EOF)")


	def save(self, dataSource=None):
		""" Ask the bizobj to commit its changes to the backend.
		"""
		self.activeControlValid()
		bizobj = self.getBizobj(dataSource)

		try:
			if self.SaveAllRows:
				bizobj.saveAll()
			else:
				bizobj.save()
				
			if self.debug:
				print "Save successful."
			self.setStatusText(_("Changes to %s saved." % (
					self.SaveAllRows and "all records" or "current record",)))
					
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
		self.activeControlValid()
		bizobj = self.getBizobj(dataSource)

		try:
			if self.SaveAllRows:
				bizobj.cancelAll()
			else:
				bizobj.cancel()
			if self.debug:
				print "Cancel successful."
			self.setStatusText(_("Changes to %s canceled." % (
					self.SaveAllRows and "all records" or "current record",)))
			self.refreshControls()
		except dException.dException, e:
			if self.debug:
				print "Cancel failed with response: %s" % str(e)
			### TODO: What should be done here? Raise an exception?
			###       Prompt the user for a response?


	def onRequery(self, event):
		""" Occurs when an EVT_MENU event is received by this form.
		"""
		self.requery()
		self.Raise()
		event.Skip()


	def requery(self, dataSource=None):
		""" Ask the bizobj to requery.
		"""
		import time

		self.activeControlValid()
		bizobj = self.getBizobj(dataSource)

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
			stop = round(time.time() - start, 3)
			if self.debug:
				print "Requery successful."
			self.setStatusText(_("%s record%sselected in %s second%s" % (
					bizobj.RowCount, 
					bizobj.RowCount == 1 and " " or "s ",
					stop,
					stop == 1 and "." or "s.")))
			self.refreshControls()

			# Notify listeners that the row number changed:
			evt = dEvents.dEvent(dEvents.EVT_ROWNUMCHANGED, self.GetId())
			self.GetEventHandler().ProcessEvent(evt)

		except dException.dException, e:
			if self.debug:
				print "Requery failed with response: %s" % str(e)
			### TODO: What should be done here? Raise an exception?
			###       Prompt the user for a response?


	def delete(self, dataSource=None, message=None):
		""" Ask the bizobj to delete the current record.
		"""
		self.activeControlValid()
		bizobj = self.getBizobj(dataSource)
		
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
					print "Delete successful."
				self.setStatusText(_("Record Deleted."))
				self.refreshControls()
				# Notify listeners that the row number changed:
				evt = dEvents.dEvent(dEvents.EVT_ROWNUMCHANGED, self.GetId())
				self.GetEventHandler().ProcessEvent(evt)
			except dException.dException, e:
				if self.debug:
					print "Delete failed with response: %s" % str(e)
				### TODO: What should be done here? Raise an exception?
				###       Prompt the user for a response?


	def deleteAll(self, dataSource=None, message=None):
		""" Ask the primary bizobj to delete all records from the recordset.
		"""
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
			except dException.dException, e:
				if self.debug:
					print "Delete All failed with response: %s" % str(e)
				### TODO: What should be done here? Raise an exception?
				###       Prompt the user for a response?


	def new(self, dataSource=None):
		""" Ask the bizobj to add a new record to the recordset.
		"""
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
			dataSource = self.getPrimaryBizobj()
		
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
					bo = self.getBizobj(dataSource, parentBizobj)
					if bo:
						return bo
			# if we got here, none were found
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
		""" Get the text to describe which record is current.
		"""
		bizobj = self.getBizobj(dataSource)
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
					'Specifies whether dataset is row- or table-buffered. (bool)')

	AskToSave = property(_getAskToSave, _setAskToSave, None, 
					'Specifies whether a save prompt appears before the data is requeried. (bool)')


if __name__ == "__main__":
	import test
	test.Test().runTest(dForm)
