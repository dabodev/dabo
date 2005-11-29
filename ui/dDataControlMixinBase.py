""" dDataControlMixin.py: Provide behavior common to all 
	data-aware dControls.
"""
import dabo, dabo.ui
import dabo.dEvents as dEvents
import dabo.dException as dException
from dabo.dLocalize import _


class dDataControlMixinBase(dabo.ui.dControlMixin):
	""" Provide common functionality for the data-aware controls."""
	def __init__(self, *args, **kwargs):
		self._inFldValid = False
		self.__src = self._srcIsBizobj = self._srcIsInstanceMethod = None
		super(dDataControlMixinBase, self).__init__(*args, **kwargs)
			
		self._value = self.Value
		self.enabled = True
		# Initialize runtime properties
		
	
	def _initEvents(self):
		super(dDataControlMixinBase, self)._initEvents()
		
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
		if not self._inFldValid:
			self._oldVal = self.Value
		self._inFldValid = False
		try:
			if self.SelectOnEntry:
				self.selectAll()
		except AttributeError:
			# only text controls have SelectOnEntry
			pass
	
	
	def __onLostFocus(self, evt):
		ok = True
		# Call the field-level validation if indicated.
		if self._oldVal != self.Value:
			if hasattr(self.Form, "validateField"):
				ok = self.Form.validateField(self)
		if ok is False:
			# If validation fails, don't write the value to the source. Also,
			# flag this field so that the gotFocus() doesn't set _oldVal
			# to the invalid value.
			self._inFldValid = True
		else:
			# Everything's hunky dory; push the value to the DataSource.
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
			if self.SelectOnEntry and self.Form.ActiveControl == self:
				self.selectAll()
		except AttributeError:
			# only text controls have SelectOnEntry
			pass 



	def getBlankValue(self):
		""" Return the empty value of the control.
		"""
		return None


	def refresh(self):
		""" Update control's value to match the current value from the source.
		"""
		if not self.DataSource or not self.DataField:
			return
		if self.Source and self._srcIsBizobj:
			try:
				self.Value = self.Source.getFieldVal(self.DataField)
				self.Enabled = self.enabled
			except (TypeError, dException.NoRecordsException):
				self.Value = self.getBlankValue()
				# Do we need to disable the control?
				#self.Enabled = False
		else:
			if self._srcIsInstanceMethod is None and self.Source is not None:
				self._srcIsInstanceMethod = eval("type(self.Source.%s)" % self.DataField) == type(self.refresh)
			if self._srcIsInstanceMethod:
				expr = "self.Source.%s()" % self.DataField
			else:
				expr = "self.Source.%s" % self.DataField
			try:
				self.Value = eval(expr)
			except:
				## Couldn't evaluate, for whatever reason. Do the same thing that we do
				## for bizobj datasources: fill in the blank value.
				self.Value = self.getBlankValue()
				#dabo.errorLog.write("Could not evaluate value for %s" % expr)
			
			
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
		""" Save any changes to the underlying source field."""
		curVal = self.Value
		ret = None
		try:
			oldVal = self._oldVal
		except AttributeError:
			oldVal = None
		
		if curVal is None or curVal != oldVal:
			if self.DataSource and self.DataField:
				src = self.Source
				if self._srcIsBizobj:
					try:
						ret = src.setFieldVal(self.DataField, curVal)
					except AttributeError:
						# Eventually, we'll want our global error handler be the one to write
						# to the errorLog, at which point we should reraise the exception as 
						# commented below. However, raising the exception here without a global
						# handler results in some ugly GTK messages and a segfault, so for now
						# let's just log the problem and let the app continue on.
						#raise AttributeError, "No source object found for datasource '%s'" % self.DataSource
						dabo.errorLog.write("No source object found for datasource '%s'" % self.DataSource)
				else:	
					# If the binding is to a method, do not try to assign to that method.
					if self._srcIsInstanceMethod is None:
						self._srcIsInstanceMethod = eval("type(src.%s)" % self.DataField) == type(self.flushValue)
					if self._srcIsInstanceMethod:
						return
					try:
						exec("src.%s = curVal" % self.DataField)
					except:
						dabo.errorLog.write("Could not bind to '%s.%s'" % (self.DataSource, self.DataField) )

			self._afterValueChanged()
		
		# In most controls, self._oldVal is set upon GotFocus. Some controls
		# like dCheckBox and dDropdownList don't emit focus events, so
		# flushValue must stand alone (those controls call flushValue() upon
		# every Hit, while other controls call flushValue() upon LostFocus. 
		# Setting _oldVal to None here ensures that any changes will get saved
		# no matter what type of control we are...
		self._oldVal = None
		return ret


	def saveValue(self):
		""" Save control's value to dApp's user settings table."""
		if self.IsSecret:
			# Don't store sensitive info
			return
		# It is too late to get Value directly (since we are being called from Destroy, and wx
		# has already released the C++ part of the object).
		value = self._value	
		if self.Application:
			if self.RegID:
				name = "%s.%s" % (self.Form.Name, self.RegID)
			else:
				name = self.getAbsoluteName()
			self.Application.setUserSetting("%s.Value" % name, value)
		
			
	def restoreValue(self):
		""" Set the control's value to the value in dApp's user settings table."""			
		if self.Application:
			if self.RegID:
				name = "%s.%s" % (self.Form.Name, self.RegID)
			else:
				name = self.getAbsoluteName()
			value = self.Application.getUserSetting("%s.Value" % name)

			if value is not None:
				try:
					self.Value = value
				except TypeError:
					self.Value = self.getBlankValue()		
			
			
	def getShortDataType(self, value):
		if isinstance(value, (int, long)):
			return "I"
		elif isinstance(value, basestring):
			return "C"
		elif isinstance(value, float):
			return "N"
		elif isinstance(value, bool):
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
			return ""
	def _setDataSource(self, value):
		# Clear any old DataSource
		self.__src = None
		self._DataSource = str(value)

	def _getDataField(self):
		try:
			return self._DataField
		except AttributeError:
			return ""
	def _setDataField(self, value):
		self._DataField = str(value)

	def _getSecret(self):
		try:
			return self._isSecret
		except AttributeError:
			self._isSecret = False
			return self._isSecret
	def _setSecret(self, val):
		self._isSecret = val

	def _getSaveRestoreValue(self):
		try:
			return self._SaveRestoreValue
		except AttributeError:
			return False
	def _setSaveRestoreValue(self, value):
		self._SaveRestoreValue = bool(value)
		
	def _getSrc(self):
		if self.__src is None:
			ds = self.DataSource
			self._srcIsBizobj = False
			if ds:
				# Source can be a bizobj, which we get from the form, or
				# another object.
				if ds.lower() == "form":
					# We're bound to the form itself
					self.__src = self.Form
				elif ds[:5] == "self.":
					# it's a locally resolvable reference.
					try: 
						self.__src = eval(ds)
					except: pass
				else:
					# See if it's a RegID reference to another object
					try:
						self.__src = self.Form.getObjectByRegID(ds)
					except:
						self.__src = None
					if self.__src is None:
						# It's a bizobj reference; get it from the Form.
						self.__src = self.Form.getBizobj(ds)
						if self.__src:
							self._srcIsBizobj = True
		return self.__src

	
	# Property definitions:
	DataSource = property(_getDataSource, _setDataSource, None,
			_("Specifies the dataset to use as the source of data.  (str)") )
	
	DataField = property(_getDataField, _setDataField, None,
			_("""Specifies the data field of the dataset to use as the source 
			of data. (str)""") )
	
	IsSecret = property(_getSecret, _setSecret, None,
			_("Flag for indicating sensitive data that is not to be persisted.   (bool)") )
			
	SaveRestoreValue = property(_getSaveRestoreValue, _setSaveRestoreValue, None, 
			_("""Specifies whether the Value of the control gets saved when 
			destroyed and restored when created. Use when the control isn't 
			bound to a dataSource and you want to persist the value, as in 
			an options dialog.  (bool)""") )
	
	Source = property(_getSrc, None, None,
			_("Reference to the object to which this control's Value is bound  (object)") )
			
	Value = property(None, None, None,
		_("Specifies the current state of the control (the value of the field). (varies)") )
