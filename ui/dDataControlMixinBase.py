""" dDataControlMixin.py: Provide behavior common to all 
	data-aware dControls.
"""
import dabo, dabo.ui
import dabo.dEvents as dEvents
import dabo.dException as dException
from dabo.dLocalize import _


class dDataControlMixinBase(dabo.ui.dControlMixin):
	""" Provide common functionality for the data-aware controls.
	"""
	
	def __init__(self, name=None, _explicitName=True):
		#dDataControlMixinBase.doDefault(name)
		super(dDataControlMixinBase, self).__init__(name, _explicitName=_explicitName)

		self._value = self.Value
		self.enabled = True

		# Initialize runtime properties
		self.bizobj = None

	
	def initEvents(self):
		#dDataControlMixinBase.doDefault()
		super(dDataControlMixinBase, self).initEvents()
		
		try:
			self.Form.bindEvent(dEvents.ValueRefresh, self.__onValueRefresh)
		except AttributeError:
			# Perhaps we aren't a child of a dForm
			pass
		
		self.bindEvent(dEvents.Create, self.__onCreate)
		self.bindEvent(dEvents.Destroy, self.__onDestroy)
		self.bindEvent(dEvents.GotFocus, self.__onGotFocus)
		self.bindEvent(dEvents.LostFocus, self.__onLostFocus)
	
		
	def __onCreate(self, evt):
		if self.SaveRestoreValue:
			self.restoreValue()
	
	
	def __onDestroy(self, evt):
		if self.SaveRestoreValue:
			self.saveValue()
	
	
	def __onGotFocus(self, evt):
		# self._oldVal will be compared to self.Value in flushValue()
		self._oldVal = self.Value

		try:
			if self.SelectOnEntry:
				self.selectAll()
		except AttributeError:
			# only text controls have SelectOnEntry
			pass

	
	def __onLostFocus(self, evt):
		self.flushValue()
		
		try:
			if self.SelectOnEntry:
				self.selectNone()
		except AttributeError:
			# only text controls have SelectOnEntry
			pass

			
	def __onValueRefresh(self, evt): 
		self.refresh()
		
		try:
			if self.SelectOnEntry and self.Form.FindFocus() == self:
				self.selectAll()
		except AttributeError:
			# only text controls have SelectOnEntry
			pass 



	def getBlankValue(self):
		""" Return the empty value of the control.
		"""
		if isinstance(self, (dabo.ui.dTextBox, dabo.ui.dEditBox) ):
			return ""
		elif isinstance(self, dabo.ui.dCheckBox):
			return False
		elif isinstance(self, dabo.ui.dSpinner):
			return 0
		else:
			return None


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
			

	def select(self, position, length):
		""" Select all text from <position> for <length> or end of string.
		
		UI lib must override.
		"""
		pass
	
	
	def selectAll(self):
		""" Select all text in the control.
		
		UI lib must override.
		"""
		pass
	
	
	def selectNone(self):
		""" Select no text in the control.
		
		UI lib must override.
		"""
		pass
	
	
	def flushValue(self):
		""" Save any changes to the underlying bizobj field.
		"""
		curVal = self.Value
		
		try:
			oldVal = self._oldVal
		except AttributeError:
			oldVal = None
		
		if curVal != oldVal:
			if self.DataSource and self.DataField:
				self.setFieldVal(curVal)
			self._afterValueChanged()
		
		# In most controls, self._oldVal is set upon GotFocus. Some controls
		# like dCheckBox on Mac and dDropdownList don't emit focus events, so
		# flushValue must stand alone (those controls call flushValue() upon
		# every Hit, while other controls call flushValue() upon LostFocus. 
		# Setting _oldVal to None here ensures that any changes will get saved
		# no matter what type of control we are...
		self._oldVal = None


	def saveValue(self):
		""" Save control's value to dApp's user settings table.
		"""
		try:
			app = self.Application
		except AttributeError:
			app = None

		# It is too late to get Value directly:		
		value = self._value	

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

			if value is not None:
				try:
					self.Value = value
				except TypeError:
					self.Value = self.getBlankValue()		
			
			
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
			dabo.infoLog.write(_("getShortDataType - unknown type: %s") % (value,))
			return "?"
			
			
	def _afterValueChanged(self):
		"""Called after the control's value has changed.
		
		This is defined as one of:
			+ the user changed the value and then the control lost focus
			+ the control's Value property was set and the value changed
			
		User code shouldn't need to access or override this.
		"""
		
		# Maintain an internal copy of the value, separate from the
		# property, so that we still have the value regardless of whether
		# or not the underlying ui object still exists (in wx at least,
		# the Destroy event fires after the c++ object is already gone,
		# so we need a copy of the value for any routine that happens
		# upon Destroy (saveValue, for instance)):
		self._value = self.Value
		
		# Raise an event so that user code can react if needed:
		self.raiseEvent(dabo.dEvents.ValueChanged)

			
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
	
	# Property definitions:
	DataSource = property(_getDataSource, _setDataSource, None,
						'Specifies the dataset to use as the source of data. (str)')
	
	DataField = property(_getDataField, _setDataField, None,
						'Specifies the data field of the dataset to use as the source of data. (str)')
	
	SaveRestoreValue = property(_getSaveRestoreValue, _setSaveRestoreValue, None, 
						'Specifies whether the Value of the control gets saved when destroyed and '
						'restored when created. Use when the control isn\'t bound to a dataSource '
						'and you want to persist the value, as in an options dialog. (bool)')
	
	Value = property(None, None, None,
		'Specifies the current state of the control (the value of the field). (varies)')
