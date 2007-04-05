import sys
import time
import wx
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
import dFormMixin as fm
import dabo.dException as dException
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


class BaseForm(fm.dFormMixin):
	"""Creates a bizobj-aware form.

	dForm knows how to handle one or more dBizobjs, providing proxy methods 
	like next(), last(), save(), and requery().
	"""
	def __init__(self, preClass, parent, properties, attProperties, *args, **kwargs):
		self.bizobjs = {}
		self._primaryBizobj = None
		
		# If this is True, a panel will be automatically added to the
		# form and sized to fill the form.
		self.mainPanel = None
		self.mkPanel = self._extractKey(attProperties, "panel", False)
		if self.mkPanel is not False:
			self.mkPanel = (self.mkPanel == "True")
		else:
			self.mkPanel = self._extractKey((kwargs, properties), "panel", False)
		
		# Use this for timing queries and other long-
		# running events
		self.stopWatch = wx.StopWatch()
		self.stopWatch.Pause()

		# Determines if the user is prompted to save changes when the form is closed
		# or a requery is about to happen.
		self._checkForChanges = True
		
		fm.dFormMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)

# 		if self.mainPanel:
# 			# Can't do this in the _afterInit, as properties haven't been
# 			# applied at that point.
# 			self.mainPanel.BackColor = self.BackColor
		
		
		# Used to override some cases where the status
		# text should be displayed despite other processes
		# trying to overwrite it
		self._holdStatusText = ""


	def beforeSetProperties(self, props):
		if "UseSizers" in props and not hasattr(self, "UseSizers"):
			del props["UseSizers"]
		
		
	def _afterInit(self):
		self.Sizer = dabo.ui.dSizer("vertical")
		self.Sizer.layout()
		if self.mkPanel:
			mp = self.mainPanel = dabo.ui.dPanel(self)
			self.Sizer.append(mp, 1, "x")
			mp.Sizer = dabo.ui.dSizer(self.Sizer.Orientation)
		super(BaseForm, self)._afterInit()
		if self.RequeryOnLoad:
			dabo.ui.callAfter(self.requery)
	
	
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
			ret = super(BaseForm, self)._beforeClose(evt)
		return ret
		
		
	def notifyUser(self, msg, title="Notice", severe=False):
		""" Displays an alert messagebox for the user. You can customize
		this in your own classes if you prefer a different display.
		"""
		if severe:
			func = dabo.ui.stop
		else:
			func = dabo.ui.info
		func(message=msg, title=title)


	def confirmChanges(self):
		"""Ask the user if they want to save changes, discard changes, or cancel.

		The user will be queried if the form's CheckForChanges property is True, and
		if there are any pending changes on the form's bizobjs as specified in the
		return value of getBizobjsToCheck().

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
		bizList = self.getBizobjsToCheck()
		changedBizList = []
		
		for biz in bizList:
			if biz and biz.isAnyChanged():
				changedBizList.append(biz)
			
		if changedBizList:
			queryMessage = self.getConfirmChangesQueryMessage(changedBizList)
			response = dabo.ui.areYouSure(queryMessage, parent=self)
			if response == None:     ## cancel
				# Don't let the form close, or requery happen
				return False
			elif response == True:   ## yes
				for biz in changedBizList:
					self.save(dataSource=biz.DataSource)
			elif response == False:  ## no
				for biz in changedBizList:
					self.cancel(dataSource=biz.DataSource)
		return True
	

	def getConfirmChangesQueryMessage(self, changedBizList):
		"""Return the "Save Changes?" message for use in the query dialog.

		The default is to return "Do you wish to save your changes?". Subclasses
		can override with whatever message they want, possibly iterating the 
		changed bizobj list to introspect the exact changes made to construct the
		message.
		"""
		return _("Do you wish to save your changes?")


	def getBizobjsToCheck(self):
		"""Return the list of bizobj's to check for changes during confirmChanges().

		The default behavior is to simply check the primary bizobj, however there 
		may be cases in subclasses where a different bizobj may be checked, or even 
		several. In those cases, override	this method and return a list of the 
		required bizobjs.
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
		return self._moveRecordPointer(bizobj.moveToRowNumber, dataSource, rowNumber)


	def _moveRecordPointer(self, func, dataSource=None, *args, **kwargs):
		""" Move the record pointer using the specified function."""
		
		biz = self.getBizobj(dataSource)
		oldRowNum = biz.RowNumber

		self.activeControlValid()
		err = self.beforePointerMove()
		if err:
			self.notifyUser(err)
			return False
		try:
			response = func(*args, **kwargs)
		except dException.NoRecordsException:
			self.setStatusText(_("No records in dataset."))
			return False
		except dException.BeginningOfFileException:
			self.setStatusText(self.getCurrentRecordText(dataSource) + " (BOF)")
			return False
		except dException.EndOfFileException:
			self.setStatusText(self.getCurrentRecordText(dataSource) + " (EOF)")
			return False
		except dException.dException, e:
			self.notifyUser(str(e))
			return False
		else:
			if biz.RowNumber != oldRowNum:
				# Notify listeners that the row number changed:
				dabo.ui.callAfter(self.raiseEvent, dEvents.RowNumChanged)
			self.update()
		self.afterPointerMove()
		return True


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

		except dException.DBQueryException, e:
			self.setStatusText(_("Save failed."))
			msg = "%s:\n\n%s" % (_("Save Failed"), e)
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
			self.update()
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
		
		if not self.confirmChanges():
			# A False from confirmChanges means "don't proceed"
			return

#		self.setStatusText(_("Please wait... requerying dataset..."))
		
		try:
			busy = dabo.ui.busyInfo(_("Please wait... requerying dataset..."))
			self.stopWatch.Start()
#			response = dProgressDialog.displayAfterWait(self, 2, bizobj.requery)
			response = bizobj.requery()
			self.stopWatch.Pause()
			elapsed = round(self.stopWatch.Time()/1000.0, 3)
			
			self.update()
			del busy

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
			self.StatusText = ""

		except dException.ConnectionLostException, e:
			msg = self._connectionLostMsg(str(e))
			self.notifyUser(msg, title=_("Data Connection Lost"), severe=True)
			self.StatusText = ""
			sys.exit()

		except dException.DBQueryException, e:
			dabo.errorLog.write(_("Database Execution failed with response: %s") % str(e))
			self.notifyUser(str(e), title=_("Database Action Failed"), severe=True)
			self.StatusText = ""

		except dException.dException, e:
			dabo.errorLog.write(_("Requery failed with response: %s") % str(e))
			self.notifyUser(str(e), title=_("Requery Not Allowed"), severe=True)
			self.StatusText = ""

		self.afterRequery()
		return ret
		

	def delete(self, dataSource=None, message=None, prompt=True):
		""" Ask the bizobj to delete the current record."""
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
			self.setStatusText(_("Nothing to delete!"))
			return
			
		err = self.beforeDelete()
		if err:
			self.notifyUser(err)
			return
		if message is None:
			message = _("This will delete the current record from %s, and cannot "
					"be canceled.\n\n Are you sure you want to do this?") % biz_caption
		if not prompt or dabo.ui.areYouSure(message, defaultNo=True, cancelButton=False):
			try:
				bizobj.delete()
				self.setStatusText(_("Record Deleted."))
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
		self.update()
		

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
		self.update()
		

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

		# Notify listeners that the row number changed:
		self.raiseEvent(dEvents.RowNumChanged)

		self.afterNew()
		self.update()
		

	def afterNew(self): pass


	def getSQL(self, dataSource=None):
		""" Get the current SQL from the bizobj."""
		return self.getBizobj(dataSource).getSQL()


	def setSQL(self, sql, dataSource=None):
		""" Set the SQL for the bizobj."""
		self.getBizobj(dataSource).setSQL(sql)
		

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
			
		if isinstance(dataSource, basestring) and \
				dataSource.lower() == "form":
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
			return True
		biz = self.getBizobj(ds)
		if not biz:
			# Now that DataSources are not always bizobjs, just return
			## No bizobj for that DataSource; record the error
			#dabo.errorLog.write("No business object found for DataSource: '%s', DataField: '%s' "
			#		% (ds, df))
			return True
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
	def _getCheckForChanges(self):
		return self._checkForChanges
			
	def _setCheckForChanges(self, value):
		self._checkForChanges = bool(value)
		

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


	def _getRequeryOnLoad(self):
		try:
			return self._requeryOnLoad
		except AttributeError:
			return False

	def _setRequeryOnLoad(self, value):
		self._requeryOnLoad = bool(value)


	def _getSaveAllRows(self):
		try:
			return self._SaveAllRows
		except AttributeError:
			return True
			
	def _setSaveAllRows(self, value):
		self._SaveAllRows = bool(value)


	# Property definitions:
	CheckForChanges = property(_getCheckForChanges, _setCheckForChanges, None, 
			_("""Specifies whether the user is prompted to save or discard changes. (bool)

			If True (the default), when operations such as requery() or the closing
			of the form are about to occur, the user will be presented with a dialog
			box asking whether to save changes, discard changes, or cancel the 
			operation that led to the dialog being presented.""") )

	PrimaryBizobj = property(_getPrimaryBizobj, _setPrimaryBizobj, None, 
			_("Reference to the primary bizobj for this form  (dBizobj)") )

	RequeryOnLoad = property(_getRequeryOnLoad, _setRequeryOnLoad, None,
			_("""Specifies whether an automatic requery happens when the 
			form is loaded.  (bool)"""))

	SaveAllRows = property(_getSaveAllRows, _setSaveAllRows, None, 
			_("Specifies whether dataset is row- or table-buffered. (bool)") )



class dForm(BaseForm, wx.Frame):
	def __init__(self, parent=None, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dForm

		if kwargs.pop("Modal", False):
			# Hack this into a wx.Dialog, for true modality
			dForm.__bases__ = (BaseForm, wx.Dialog)
			preClass = wx.PreDialog
			self._modal = True
		else:
			# Normal dForm
			if dabo.settings.MDI and isinstance(parent, wx.MDIParentFrame):
				# Hack this into an MDI Child:
				dForm.__bases__ = (BaseForm, wx.MDIChildFrame)
				preClass = wx.PreMDIChildFrame
				self._mdi = True
			else:
				# This is a normal SDI form:
				dForm.__bases__ = (BaseForm, wx.Frame)
				preClass = wx.PreFrame
				self._mdi = False

		## (Note that it is necessary to run the above blocks each time, because
		##  we are modifying the dForm class definition globally.)
		BaseForm.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)

	def Show(self, show=True, *args, **kwargs):
		self._gtk_show_fix(show)
		dForm.__bases__[-1].Show(self, show, *args, **kwargs)

	def Layout(self):
		super(dForm, self).Layout()
		wx.CallAfter(self.update)

	def _getModal(self):
		return getattr(self, "_modal", False)

	def _getVisible(self):
		return self.IsShown()
	
	def _setVisible(self, val):
		if self._constructed():
			val = bool(val)
			if val and self.Modal:
				self.ShowModal()
			else:
				self.Show(val)
		else:
			self._properties["Visible"] = val

	Modal = property(_getModal, None, None,
			_("""Specifies whether this dForm is modal or not  (bool)

			A modal dForm runs its own event loop, blocking program flow until the
			form is hidden or closed, exactly like a dDialog does it. This property
			may only be sent to the constructor, and once instantiated you may not
			change the modality of a form. For example,
					frm = dabo.ui.dForm(Modal=True)
			will create a modal form.

			Note that a modal dForm is actually a dDialog, and as such does not
			have the ability to contain MenuBars, StatusBars, or ToolBars."""))

	Visible = property(_getVisible, _setVisible, None,
			_("Specifies whether the form is shown or hidden.  (bool)") )

	

class dToolForm(BaseForm, wx.MiniFrame):
	def __init__(self, parent=None, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dToolForm
		preClass = wx.PreMiniFrame
		self._mdi = False
		style = kwargs.get("style", 0)
		kwargs["style"] = style | wx.RESIZE_BORDER | wx.CAPTION | wx.MINIMIZE_BOX | \
				wx.MAXIMIZE_BOX | wx.CLOSE_BOX		
		kwargs["TinyTitleBar"] = True
		kwargs["ShowStatusBar"] = False
		kwargs["ShowToolBar"] = False
		BaseForm.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)

	def Show(self, show=True, *args, **kwargs):
		self._gtk_show_fix(show)
		wx.MiniFrame.Show(self, show, *args, **kwargs)



class dBorderlessForm(BaseForm, wx.Frame):
	def __init__(self, parent=None, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dBorderlessForm
		style = kwargs.get("style", 0)
		kwargs["style"] = style | wx.NO_BORDER
		kwargs["ShowStatusBar"] = False
		kwargs["ShowSystemMenu"] = False
		kwargs["MenuBarClass"] = None
		preClass = wx.PreFrame
		BaseForm.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)
	
	def Show(self, show=True, *args, **kwargs):
		self._gtk_show_fix(show)
		wx.Frame.Show(self, show, *args, **kwargs)


class _dForm_test(dForm):
	def afterInit(self):
		self.Caption = _("Regular Form")
	def onActivate(self, evt):
		print _("Activate")
	def onDeactivate(self, evt):
		print _("Deactivate")
					
class _dBorderlessForm_test(dBorderlessForm):
	def afterInit(self):
		self.btn = dabo.ui.dButton(self, Caption=_("Close Borderless Form"))
		self.Sizer.append(self.btn, halign="Center", valign="middle")
		self.layout()
		self.btn.bindEvent(dEvents.Hit, self.close)
		dabo.ui.callAfter(self.setSize)
	
	def setSize(self):
		self.Width, self.Height = self.btn.Width+60, self.btn.Height+60
		self.layout()
		self.Centered = True
		
		
					
if __name__ == "__main__":
	import test
	test.Test().runTest(_dForm_test)
	test.Test().runTest(_dBorderlessForm_test)

