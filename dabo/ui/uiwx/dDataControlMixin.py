# -*- coding: utf-8 -*-
import dabo
from dabo.ui.dDataControlMixinBase import dDataControlMixinBase
from dabo.dLocalize import _
from dabo.lib.utils import ustr
from dabo.ui import makeDynamicProperty



class dDataControlMixin(dDataControlMixinBase):
	def _onWxHit(self, evt, *args, **kwargs):
		self._userChanged = True  ## set the dirty flag so that InteractiveChange can be raised.
		super(dDataControlMixin, self)._onWxHit(evt, *args, **kwargs)


	def select(self, position, length):
		"""Select all text from <position> for <length> or end of string."""
		try:
			self.SetInsertionPoint(1)
			self.SetSelection(position, length)
		except AttributeError:
			# Only works for text controls
			pass


	def selectAll(self):
		"""Select all text in the control."""
		try:
			self.SetInsertionPoint(1)   # Best of all worlds (really)
			self.SetSelection(-1,-1)    # select all text
		except AttributeError:
			# Only works for text controls
			pass


	def selectNone(self):
		"""Select no text in the control."""
		try:
			self.SetSelection(0,0)
		except AttributeError:
			# Only works for text controls
			pass


	def _coerceValue(self, val, oldval):
		convTypes = (str, unicode, int, float, long, complex)
		oldType = type(oldval)
		if isinstance(val, convTypes) and isinstance(oldval, basestring):
			val = ustr(val)
		elif isinstance(oldval, int) and isinstance(val, basestring):
			val = int(val if val else "0")
		elif isinstance(oldval, int) and isinstance(val, bool):
			# convert bool to int (original field val was bool, but UI
			# changed to int.
			val = int(val)
		elif isinstance(oldval, int) and isinstance(val, long):
			# convert long to int (original field val was int, but UI
			# changed to long.
			val = int(val)
		elif isinstance(oldval, long) and isinstance(val, int):
			# convert int to long (original field val was long, but UI
			# changed to int.
			val = long(val)
		return val


	def _getValue(self):
		return self.GetValue()

	def _setValue(self, val):
		if self._constructed():
			currVal = self.Value
			if type(currVal) != type(val):
				val = self._coerceValue(val, currVal)
			if (type(currVal) != type(val) or currVal != val):
				setter = self.SetValue
				if hasattr(self, "ChangeValue"):
					setter = self.ChangeValue
				try:
					setter(val)
				except (TypeError, ValueError), e:
					nm = self._name
					dabo.log.error(_("Could not set value of %(nm)s to %(val)s. Error message: %(e)s")
							% locals())
			self._afterValueChanged()
		else:
			self._properties["Value"] = val


	Value = property(_getValue, _setValue, None,
			_("""Specifies the current state of the control (the value of the field).  (varies)"""))


	DynamicValue = makeDynamicProperty(Value)

