""" dDataControlMixin.py: Provide behavior common to all 
	data-aware dControls.
"""
import wx
import dabo
import dPemMixin as pm
import dEvents
import dabo.dException as dException
from dabo.dLocalize import _

class dDataControlMixin(pm.dPemMixin):
	""" Provide common functionality for the data-aware controls.
	"""
	def __init__(self):
		pm.dPemMixin.__init__(self)

		self._oldVal = self.Value
		self.enabled = True

		# Initialize runtime properties
		self.bizobj = None


	def initEvents(self):
		pass
		
		
	def onCreate(self, event):
		if self.debug:
			dabo.infoLog.write(_("onCreate received by %s") % self.Name)
		if self.SaveRestoreValue:
			self.restoreValue()
		event.Skip()
	
	def onDestroy(self, event):
		if self.debug:
			dabo.infoLog.write(_("onDestroy received by %s") % self.Name)
		if self.SaveRestoreValue:
			self.saveValue()
		event.Skip()
	

	def getBlankValue(self):
		""" Return the empty value of the control.
		"""
		if isinstance(self, wx.TextCtrl):
			return ""
		elif isinstance(self, wx.CheckBox):
			return False
		elif isinstance(self, wx.SpinCtrl):
			return 0


	def getFieldVal(self):
		""" Ask the bizobj what the current value of the field is. 
		"""
		if not self.bizobj:
			# Ask the form for the bizobj reference, and cache for next time
			self.bizobj = self.Form.getBizobj(self.DataSource)
		return self.bizobj.getFieldVal(self.DataField)


	def setFieldVal(self, value):
		""" Ask the bizobj to update the field value. 
		"""
		if not self.bizobj:
			# Ask the form for the bizobj reference, and cache for next time
			self.bizobj = self.Form.getBizobj(self.DataSource)
		try:
			return self.bizobj.setFieldVal(self.DataField, value)
		except AttributeError:
			# Eventually, we'll want our global error handler be the one to write
			# to the errorLog, at which point we should reraise the exception as 
			# commented below. However, raising the exception here without a global
			# handler results in some ugly GTK messages and a segfault, so for now
			# let's just log the problem and let the app continue on.
			#raise AttributeError, "There is no bizobj for datasource '%s'" % self.DataSource
			dabo.errorLog.write("There is no bizobj for datasource '%s'" % self.DataSource)


	def refresh(self):
		""" Update control's value to match the current value from the bizobj.
		"""
		if self.DataSource and self.DataField:
			try:
				self.Value = self.getFieldVal()
				self.Enabled = self.enabled
			except (TypeError, dException.NoRecordsException):
				self.Value = self.getBlankValue()
				# Do we need to disable the control?
				#self.Enabled = False
			self._oldVal = self.Value
			

	def onValueRefresh(self, event): 
		""" Occurs when the field value has potentially changed.
		"""
		if self.debug:
			dabo.infoLog.write(_("onValueRefresh received by %s") % (self.GetName(),))
		self.refresh()
		
		try:
			if self.SelectOnEntry and self.Form.FindFocus() == self:
				self.selectAll()
		except AttributeError:
			# only text controls have SelectOnEntry
			pass 
		event.Skip()


	def selectAll(self):
		""" Select all text in the control.
		"""
		self.SetInsertionPoint(1)   # Best of all worlds (really)
		self.SetSelection(-1,-1)    # select all text


	def onGotFocus(self, event):
		""" Occurs when the control receives the keyboard focus.
		"""
		if self.debug:
			dabo.infoLog.write(_("onGotFocus received by %s") % self.Name)

		self._oldVal = self.Value

		try:
			if self.SelectOnEntry:
				self.selectAll()
		except AttributeError:
			# only text controls have SelectOnEntry
			pass
		event.Skip()


	def onLostFocus(self, event):
		""" Occurs when the control loses the keyboard focus.
		"""
		if self.debug:
			dabo.infoLog.write(_("onLostFocus received by %s") % self.Name)

		self.flushValue()
		
		try:
			if self.SelectOnEntry:
				self.SetSelection(0,0)     # select no text in text box
		except AttributeError:
			# only text controls have SelectOnEntry
			pass
		event.Skip()
			

	def flushValue(self):
		""" Save any changes to the underlying bizobj field.
		"""
		
		curVal = self.Value
		if curVal != self._oldVal and self.DataSource and self.DataField:
			self.setFieldVal(curVal)
		else:
			self.Value = curVal
		self._oldVal = curVal


	def saveValue(self):
		""" Save control's value to dApp's user settings table.
		"""
		try:
			app = self.Application
		except AttributeError:
			app = None

		# It is too late to get Value directly:		
		value = self._oldVal	
		
		if app:
			name = self.getAbsoluteName()
			app.setUserSetting("%s.Value" % name, self.getShortDataType(value), value)
		
			
	def restoreValue(self):
		""" Set the control's value to the value in dApp's user settings table.
		"""
		try:
			app = self.Application
		except AttributeError:
			app = None
			
		if app:
			name = self.getAbsoluteName()
			value = app.getUserSetting("%s.Value" % name)

			try:
				self.Value = value
			except TypeError:
				self.Value = self.getBlankValue()		
			self._oldVal = self.Value
			
			
	def getShortDataType(self, value):
		if type(value) in [type(int()), type(long())]:
			return "I"
		elif type(value) in [type(str()), type(unicode())]:
			return "C"
		elif type(value) in [type(float()), ]:
			return "N"
		elif type(value) in [type(bool()), ]:
			return "L"
		else:
			dabo.infoLog.write(_("getShortDataType - unknown type:"), self, value)
			return "?"
			
	
	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getDataSource(self):
		try:
			return self._DataSource
		except AttributeError:
			return ''
	def _setDataSource(self, value):
		self._DataSource = str(value)

	def _getDataField(self):
		try:
			return self._DataField
		except AttributeError:
			return ''
	def _setDataField(self, value):
		self._DataField = str(value)

	def _getSaveRestoreValue(self):
		try:
			return self._SaveRestoreValue
		except AttributeError:
			return False
	def _setSaveRestoreValue(self, value):
		self._SaveRestoreValue = bool(value)
	
	def _getValue(self):
		return self.GetValue()
		
	def _setValue(self, value):
		self.SetValue(value)
		self.raiseEvent(dEvents.ValueChanged)

	# Property definitions:
	DataSource = property(_getDataSource, _setDataSource, None,
						'Specifies the dataset to use as the source of data. (str)')
	DataField = property(_getDataField, _setDataField, None,
						'Specifies the data field of the dataset to use as the source of data. (str)')
	SaveRestoreValue = property(_getSaveRestoreValue, _setSaveRestoreValue, None, 
						'Specifies whether the Value of the control gets saved when destroyed and '
						'restored when created. Use when the control isn\'t bound to a dataSource '
						'and you want to persist the value, as in an options dialog. (bool)')
	Value = property(_getValue, _setValue, None,
						'Specifies the current state of the control (the value of the field). (varies)')
