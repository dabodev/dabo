# -*- coding: utf-8 -*-
"""dDataControlMixin.py: Provide behavior common to all	data-aware dControls."""
import dabo
import dabo.ui
import dabo.dEvents as dEvents
import dabo.dException as dException
from dabo.dObject import dObject
from dabo.dPref import dPref
from dabo.dLocalize import _
from dabo.lib.utils import ustr



class dDataControlMixinBase(dabo.ui.dControlMixin):
	"""Provide common functionality for the data-aware controls."""
	def __init__(self, *args, **kwargs):
		self._deriveTextLengthFromSource = dabo.dTextBox_DeriveTextLengthFromSource
		self._disableOnEmptyDataSource = dabo.autoDisableDataControls
		self._fldValidFailed = False
		# Control enabling/disabling on empty data source helper attribute.
		self._dsDisabled = False
		self.__src = self._srcIsBizobj = self._srcIsInstanceMethod = None
		self._designerMode = None
		self._oldVal = None
		self._userChanged = False
		# Flags to avoid calling flushValue() when it is not needed.
		self._inDataUpdate = False
		self._from_flushValue = False

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
		if not self:
			return
		if self.SaveRestoreValue:
			self.saveValue()


	def __onGotFocus(self, evt):
		self._gotFocus()


	def __onLostFocus(self, evt):
		if not self:
			return
		if self._lostFocus() is False:
			evt.stop()


	def _gotFocus(self):
		# self._oldVal will be compared to self.Value in flushValue()
		if not getattr(self, "_inFlush", False):
			if not self._fldValidFailed:
				self._oldVal = self.Value
			self._fldValidFailed = False
			# Reset flushing flag.
			self._from_flushValue = False
		try:
			if self.SelectOnEntry:
				self.selectAll()
		except AttributeError:
			# only text controls have SelectOnEntry
			pass


	def _lostFocus(self):
		if not self:
			return
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
		"""Return the empty value of the control."""
		return None


	def _verifyEnabledStatus(self, enable):
		if self.DisableOnEmptyDataSource:
			if enable:
				if self._dsDisabled:
					self._dsDisabled = False
					self.Enabled = True
			else:
				if not self._dsDisabled:
					self._dsDisabled = True
					self.Enabled = False


	def update(self):
		"""Update control's value to match the current value from the source."""
		# We need to do the data handling stuff before calling super()
		self.__dataUpdate()
		# Update selection after Value property update.
		if getattr(self, "SelectOnEntry", False) and self.Form.ActiveControl == self:
			self.selectAll()
		super(dDataControlMixinBase, self).update()


	def __dataUpdate(self):
		"""This handles all the value updating from the data source."""
		if not self.DataField or not (self.DataSource or isinstance(self.DataSource, dPref)):
			return
		if self._DesignerMode:
			return

		src = self.Source
		if src and self._srcIsBizobj:
			self._inDataUpdate = True
			try:
				self.Value = src.getFieldVal(self.DataField)
				self._verifyEnabledStatus(True)
			except dException.NoRecordsException:
				self.Value = self.getBlankValue()
				self._verifyEnabledStatus(False)
			except (TypeError):
				self.Value = self.getBlankValue()
				self._verifyEnabledStatus(True)
			except dException.FieldNotFoundException:
				# See if DataField refers to an attribute of the bizobj:
				att = getattr(src, self.DataField, None)
				if callable(att):
					self.Value = method()
				else:
					self.Value = att
				self._verifyEnabledStatus(True)
			self._inDataUpdate = False
		else:
			if self._srcIsInstanceMethod is None and src is not None:
				self._srcIsInstanceMethod = False
				if not isinstance(src, basestring):
					att = getattr(src, self.DataField, None)
					if att is not None:
						self._srcIsInstanceMethod = callable(att)

			if src is None:
				# Could be testing
				return
			try:
				srcatt = getattr(src, self.DataField)
			except AttributeError:
				# This happens in design tools, where a control might bind to a property
				# that the current object doesn't have.
				return

			self._inDataUpdate = True
			if self._srcIsInstanceMethod:
				try:
					self.Value = srcatt()
				except dException.NoRecordsException:
					## Couldn't run the method. If it was due to there being no records
					## in the bizobj, fill in the blank value.
					self.Value = self.getBlankValue()
			else:
				self.Value = srcatt
			self._inDataUpdate = False
		self._oldVal = self.Value


	def select(self, position, length):
		"""
		Select all text from <position> for <length> or end of string.

		UI lib must override.
		"""
		pass


	def selectAll(self):
		"""
		Select all text in the control.

		UI lib must override.
		"""
		pass


	def selectNone(self):
		"""
		Select no text in the control.

		UI lib must override.
		"""
		pass


	def flushValue(self):
		"""
		Save any changes to the underlying source field. First check to make sure
		that any changes are validated.
		"""
		if self._from_flushValue:
			return True
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

		##- pkm 2010-05-26: If oldVal is None and curVal is None, I don't see why we would
		##-                 think the value was changed. Commenting this out makes
		##-                 dDropdownList behave better, in that it doesn't raise ValueChanged
		##-                 when the oldVal was None and the curVal is None.
		##- #if oldVal is None and curVal is None:
		##-	# Could be changed and we just don't know it...
		##- #	isChanged = True
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
			# In some situations, e.g. if control is bound to widget property, changes of property
			# value can cause recursive call to the flushValue() method.
			# To prevent such situation we have to check the _from_flushValue attribute at the beginning.
			self._from_flushValue = True
			if not self._DesignerMode:
				if (self.DataSource or isinstance(self.DataSource, dPref)) and self.DataField:
					src = self.Source
					if self._srcIsBizobj:
						try:
							ret = src.setFieldVal(self.DataField, curVal)
						except dException.FieldNotFoundException:
							# First see if DataField refers to an attribute of the bizobj. If so, if it is
							# a method, it is read-only, so do not try to assign to it. Otherwise, set
							# the attribute to the value.
							att = getattr(self.Source, self.DataField, None)
							if att is None:
								raise
							if callable(att):
								return
							setattr(self.Source, self.DataField, curVal)
						except (dException.NoRecordsException, dException.RowNotFoundException):
							# UI called flushValue() when there wasn't a valid record active.
							# Treat as spurious and ignore.
							pass
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
								dabo.log.error("Could not bind to '%s.%s'\nReason: %s" % (self.DataSource, self.DataField, e))
						else:
							# The source is a direct object reference
							try:
								src.__setattr__(self.DataField, curVal)
							except StandardError, e:
								if hasattr(self.DataSource, "_name"):
									nm = self.DataSource._name
								else:
									nm = ustr(self.DataSource)
								dabo.log.error("Could not bind to '%s.%s'\nReason: %s" % (nm, self.DataField, e))
			self._oldVal = curVal
			self._afterValueChanged()
			self._from_flushValue = False
			# Raise an event so that user code can react if needed:
			if self._userChanged:
				self._userChanged = False
				self.raiseEvent(dEvents.InteractiveChange, oldVal=oldVal)
			self.raiseEvent(dEvents.ValueChanged)
		return ret


	def saveValue(self):
		"""Save control's value to dApp's user settings table."""
		if self._DesignerMode:
			# Don't bother in design mode.
			return
		app = self.Application
		if app:
			if self.IsSecret:
				# Don't store sensitive info until...
				if self.PersistSecretData:
					value = app.encrypt(self._value)
				else:
					return
			else:
				value = self._value  ## on Win, the C++ object is already gone
			if self.RegID:
				name = "%s.%s" % (self.Form.Name, self.RegID)
			else:
				name = self.getAbsoluteName()
			app.setUserSetting("%s.Value" % name, value)


	def restoreValue(self):
		"""Set the control's value to the value in dApp's user settings table."""
		app = self.Application
		if app:
			if self.RegID:
				name = "%s.%s" % (self.Form.Name, self.RegID)
			else:
				name = self.getAbsoluteName()
			value = app.getUserSetting("%s.Value" % name)

			if value is not None:
				if self.IsSecret and self.PersistSecretData:
					value = app.decrypt(value)
				try:
					self.Value = value
				except (ValueError, TypeError), e:
					dabo.log.error(e)


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
			dabo.log.info(_("getShortDataType - unknown type: %s") % (value,))
			return "?"


	def _afterValueChanged(self):
		"""
		Called after the control's value has changed.

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

		if self._inDataUpdate or self._from_flushValue:
			return

		if (self.Form.ActiveControl != self
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
			return self._dataSource
		except AttributeError:
			return ""

	def _setDataSource(self, val):
		# There can be race conditions where an object's DataSource is being set
		# at the same time as other properties, such as when these are all set at
		# instantiation. There can be cases, such as list controls, where the Choices
		# or Keys gets set after the DataSource/DataField props, leading to the
		# "Value not present" types of errors. By setting DataSource last, through
		# the callAfter, the race condition should be avoided.
		def _delayedSetDataSource():
			# Clear any old DataSource
			self.__src = None
			self._oldVal = None
			self._dataSource = val
			self.update()
		dabo.ui.callAfter(_delayedSetDataSource)


	def _getDataField(self):
		try:
			return self._DataField
		except AttributeError:
			return ""

	def _setDataField(self, value):
		self._oldVal = None
		self._DataField = ustr(value)


	def _getDesignerMode(self):
		if self._designerMode is None:
			try:
				self._designerMode = self.Form._designerMode
			except AttributeError:
				self._designerMode = False
		return self._designerMode


	def _getDisableOnEmptyDataSource(self):
		return getattr(self, "_disableOnEmptyDataSource", False)

	def _setDisableOnEmptyDataSource(self, val):
		self._disableOnEmptyDataSource = val


	def _getPersistSecretData(self):
		return getattr(self, "_persistSecretData", False)

	def _setPersistSecretData(self, val):
		self._persistSecretData = bool(val)


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


	def _getSource(self):
		if self.__src is None:
			ds = self.DataSource
			self._srcIsBizobj = False
			if (ds or isinstance(ds, dPref)):
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
				elif callable(ds):
					# Instead of a fixed source, call the function to determine the source.
					# We *don't* want to store the result in self.__src!
					return ds()
				else:
					# It's an object reference
					self.__src = ds
					if not isinstance(ds, (dObject, dPref)):
						# Warn about possible unsupported behavior.
						dabo.log.info(_("DataSource '%s' does not inherit from a proper Dabo class. This may result in unsupported problems.") % ds.__repr__())
					else:
						self._srcIsBizobj = isinstance(ds, dabo.biz.dBizobj)
				# This allow to use bizobj attribute as data field, instead of table field.
				# Also fix r6665 issue when NoRecordsException is raised before FieldNotFoundException exception.
				# It's tricky, because object attribute/property takes precedence before data field of the same name.
				if self._srcIsBizobj:
					self._srcIsBizobj = not hasattr(self.__src, self.DataField)
			if self._srcIsBizobj and self._deriveTextLengthFromSource and \
					hasattr(self, "TextLength"):
				field = self.DataField
				for descr in self.__src.DataStructure:
					if descr[0] == field:
						if descr[1] == "C":
							self.TextLength = descr[5]
						break
		return self.__src


	# Property definitions:
	DataSource = property(_getDataSource, _setDataSource, None,
			_("Specifies the dataset to use as the source of data.  (str)"))

	DataField = property(_getDataField, _setDataField, None,
			_("""Specifies the data field of the dataset to use as the source
			of data. (str)"""))

	_DesignerMode = property(_getDesignerMode, None, None,
			_("""When True, the control is not running live, but being used
			in design mode. Default=False.  (bool)"""))

	DisableOnEmptyDataSource = property(_getDisableOnEmptyDataSource, _setDisableOnEmptyDataSource, None,
			_("""When True and the DataSource is an empty dataset (it must be a dBizobj instance),
			control is disabled for interactive editing. Default=False.  (bool)"""))

	IsSecret = property(_getSecret, _setSecret, None,
			_("""Flag for indicating sensitive data, such as Password field, that is not
			to be persisted. Default=False.  (bool)"""))

	PersistSecretData = property(_getPersistSecretData, _setPersistSecretData, None,
			_("""If True, allow persisting the secret data in encrypted form.
			Warning! Security of your data strongly depends on used encryption algorithms!
			Default=False.  (bool)"""))

	SaveRestoreValue = property(_getSaveRestoreValue, _setSaveRestoreValue, None,
			_("""Specifies whether the Value of the control gets saved when
			destroyed and restored when created. Use when the control isn't
			bound to a dataSource and you want to persist the value, as in
			an options dialog. Default=False.  (bool)"""))

	Source = property(_getSource, None, None,
			_("Reference to the object to which this control's Value is bound  (object)"))

	Value = property(None, None, None,
			_("Specifies the current state of the control (the value of the field). (varies)"))
