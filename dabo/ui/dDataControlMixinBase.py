# -*- coding: utf-8 -*-
""" dDataControlMixin.py: Provide behavior common to all
	data-aware dControls.
"""
import dabo, dabo.ui
import dabo.dEvents as dEvents
import dabo.dException as dException
from dabo.dObject import dObject
from dabo.dPref import dPref
from dabo.dLocalize import _


class dDataControlMixinBase(dabo.ui.dControlMixin):
	""" Provide common functionality for the data-aware controls."""
	def __init__(self, *args, **kwargs):
		self._fldValidFailed = False
		self.__src = self._srcIsBizobj = self._srcIsInstanceMethod = None
		self._designerMode = None
		self._oldVal = None
		self._userChanged = False

		dabo.ui.dControlMixin.__init__(self, *args, **kwargs)

		self._value = self.Value
		self._enabled = True
		# Initialize runtime properties


	def _initEvents(self):
		super(dDataControlMixinBase, self)._initEvents()

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
		self._gotFocus()


	def __onLostFocus(self, evt):
		if self._lostFocus() is False:
			evt.stop()


	def _gotFocus(self):
		# self._oldVal will be compared to self.Value in flushValue()
		if not self._fldValidFailed:
			self._oldVal = self.Value
		self._fldValidFailed = False
		try:
			if self.SelectOnEntry:
				self.selectAll()
		except AttributeError:
			# only text controls have SelectOnEntry
			pass


	def _lostFocus(self):
		if self.flushValue() is False:
			# Field validation failed
			self._fldValidFailed = True			
			return False
		try:
			if self.SelectOnEntry:
				self.selectNone()
		except AttributeError:
			# only text controls have SelectOnEntry
			pass


	def getBlankValue(self):
		""" Return the empty value of the control."""
		return None


	def update(self):
		""" Update control's value to match the current value from the source."""
		# We need to do the data handling stuff before calling super()
		self.__dataUpdate()
		super(dDataControlMixinBase, self).update()


	def __dataUpdate(self):
		"""This handles all the value updating from the data source."""
		if getattr(self, "SelectOnEntry", False) and self.Form.ActiveControl == self:
			self.selectAll()

		if not self.DataSource or not self.DataField:
			return
		if self._DesignerMode:
			return

		src = self.Source
		if src and self._srcIsBizobj:
			# First see if DataField refers to a method of the bizobj:
			method = getattr(src, self.DataField, None)
			if callable(method):
				self.Value = method()
			else:
				try:
					self.Value = src.getFieldVal(self.DataField)
				except (TypeError, dException.NoRecordsException):
					self.Value = self.getBlankValue()
		else:
			if self._srcIsInstanceMethod is None and src is not None:
				if isinstance(src, basestring):
					self._srcIsInstanceMethod = False
				else:
					self._srcIsInstanceMethod = callable(getattr(src, self.DataField))

			if src is None:
				# Could be testing
				return
			try:
				srcatt = getattr(src, self.DataField)
			except AttributeError:
				# This happens in design tools, where a control might bind to a property
				# that the current object doesn't have.
				return

			if self._srcIsInstanceMethod:
				try:
					self.Value = srcatt()
				except dException.NoRecordsException:
					## Couldn't run the method. If it was due to there being no records
					## in the bizobj, fill in the blank value.
					self.Value = self.getBlankValue()
			else:
				self.Value = srcatt


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
		""" Save any changes to the underlying source field. First check to make sure
		that any changes are validated.
		"""
		# We need to test empty oldvals because of the way that textboxes work; they
		# can set _oldVal to "" before the actual Value is set.
		if (not self._oldVal) or (self._oldVal != self.Value):
			try:
				if not self.Form.validateField(self):
					# Validation failed; the form will handle notifying the user
					return False
			except AttributeError:
				# Form doesn't have a validateField() method
				pass
		curVal = self.Value
		ret = None
		isChanged = False
		oldVal = self._oldVal

		if self._userChanged:
			self.raiseEvent(dabo.dEvents.InteractiveChange, oldVal=oldVal)
			self._userChanged = False
		
		if oldVal is None and curVal is None:
			# Could be changed and we just don't know it...
			isChanged = True
		if isinstance(self, (dabo.ui.dToggleButton,)):
			# These classes change their value before the GotFocus event
			# can store the oldval, so always flush 'em.
			oldVal = None
		if not isChanged:
			if isinstance(curVal, float) and isinstance(oldVal, float):
				# If it is a float, make sure that it has changed by more than the
				# rounding error.
				isChanged = (abs(curVal - oldVal) > 0.0000001)
			else:
				isChanged = (curVal != oldVal)
		if isChanged:
			if not self._DesignerMode:
				if self.DataSource and self.DataField:
					src = self.Source
					if self._srcIsBizobj:
						# First see if DataField refers to a method of the bizobj, in which
						# case do not try to assign to it:
						method = getattr(self.Source, self.DataField, None)
						if method is None:
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
							if isinstance(self.DataSource, basestring):
								self._srcIsInstanceMethod = False
							else:
								self._srcIsInstanceMethod = callable(getattr(src, self.DataField))
						if self._srcIsInstanceMethod:
							return
						if isinstance(src, basestring):
							try:
								exec ("src.%s = curVal" % self.DataField)
							except StandardError, e:
								dabo.errorLog.write("Could not bind to '%s.%s'\nReason: %s" % (self.DataSource, self.DataField, e) )
						else:
							# The source is a direct object reference
							try:
								src.__setattr__(self.DataField, curVal)
							except StandardError, e:
								if hasattr(self.DataSource, "_name"):
									nm = self.DataSource._name
								else:
									nm = str(self.DataSource)
								dabo.errorLog.write("Could not bind to '%s.%s'\nReason: %s" % (nm, self.DataField, e) )
				self._oldVal = curVal
			self._afterValueChanged(_from_flushValue=True)

			# Raise an event so that user code can react if needed:
			dabo.ui.callAfterInterval(200, self.raiseEvent, dabo.dEvents.ValueChanged)
		return ret


	def saveValue(self):
		""" Save control's value to dApp's user settings table."""
		if self.IsSecret:
			# Don't store sensitive info
			return
		if self._DesignerMode:
			# Don't bother in design mode.
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


	def _afterValueChanged(self, _from_flushValue=False):
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

		if not _from_flushValue and (self.Form.ActiveControl != self
				or not getattr(self, "_flushOnLostFocus", False)):
			# Value was changed programatically, and flushValue won't ever be
			# called automatically (either the control won't flush itself upon
			# LostFocus, or the control isn't the active control so the GotFocus/
			# LostFocus mechanism won't recognize the change), so do it now.
			self.flushValue()

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
		self._oldVal = None
		self._DataSource = value


	def _getDataField(self):
		try:
			return self._DataField
		except AttributeError:
			return ""

	def _setDataField(self, value):
		self._oldVal = None
		self._DataField = str(value)


	def _getDesignerMode(self):
		if self._designerMode is None:
			try:
				self._designerMode = self.Form._designerMode
			except AttributeError:
				self._designerMode = False
		return self._designerMode


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
				# First, see if it's a string
				if isinstance(ds, basestring):
					# Source can be a bizobj, which we get from the form, or
					# another object.
					if ds.lower() == "form":
						# We're bound to the form itself
						self.__src = self.Form
					elif ds.startswith("self."):
						# it's a locally resolvable reference.
						def resolveObjRef(txt, ref=None):
							sp = txt.split(".", 1)
							if ref is None:
								ref = eval(sp[0])
								return resolveObjRef(sp[1], ref)
							else:
								try:
									ref = getattr(ref, sp[0])
								except AttributeError:
									return None
								if len(sp) > 1:
									return resolveObjRef(sp[1], ref)
								else:
									return ref
						nonself = ds.split(".", 1)[1]
						self.__src = resolveObjRef(nonself, self)
						self._srcIsBizobj = isinstance(self.__src, dabo.biz.dBizobj)
					else:
						# See if it's a RegID reference to another object
						self.__src = self.Form.getObjectByRegID(ds)
						if self.__src is None:
							# It's a bizobj reference; get it from the Form. Note that we could
							# be a control in a dialog, which is in a form.
							form = self.Form
							while form is not None:
								try:
									self.__src = form.getBizobj(ds)
									break
								except AttributeError:
									form = form.Form
							if self.__src:
								self._srcIsBizobj = True
				else:
					# It's an object reference
					self.__src = ds
					self._srcIsInstanceMethod = False
					if not isinstance(ds, (dObject, dPref)):
						# Warn about possible unsupported behavior.
						dabo.infoLog.write(_("DataSource '%s' does not inherit from a proper Dabo class. This may result in unsupported problems.") % ds.__repr__())
					else:
						self._srcIsBizobj = isinstance(ds, dabo.biz.dBizobj)
		return self.__src


	# Property definitions:
	DataSource = property(_getDataSource, _setDataSource, None,
			_("Specifies the dataset to use as the source of data.  (str)") )

	DataField = property(_getDataField, _setDataField, None,
			_("""Specifies the data field of the dataset to use as the source
			of data. (str)""") )

	_DesignerMode = property(_getDesignerMode, None, None,
			_("""When True, the control is not running live, but being used
			in design mode. Default=False.  (bool)"""))

	IsSecret = property(_getSecret, _setSecret, None,
			_("""Flag for indicating sensitive data, such as Password field, that is not 
			to be persisted. Default=False.  (bool)""") )

	SaveRestoreValue = property(_getSaveRestoreValue, _setSaveRestoreValue, None,
			_("""Specifies whether the Value of the control gets saved when
			destroyed and restored when created. Use when the control isn't
			bound to a dataSource and you want to persist the value, as in
			an options dialog. Default=False.  (bool)""") )

	Source = property(_getSrc, None, None,
			_("Reference to the object to which this control's Value is bound  (object)") )

	Value = property(None, None, None,
			_("Specifies the current state of the control (the value of the field). (varies)") )
