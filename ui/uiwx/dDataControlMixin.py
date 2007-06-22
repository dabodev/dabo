# -*- coding: utf-8 -*-
import dabo
from dabo.ui.dDataControlMixinBase import dDataControlMixinBase
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


class dDataControlMixin(dDataControlMixinBase):
	def select(self, position, length):
		""" Select all text from <position> for <length> or end of string."""
		try:
			self.SetInsertionPoint(1)
			self.SetSelection(position, length)
		except AttributeError:
			# Only works for text controls
			pass


	def selectAll(self):
		""" Select all text in the control."""
		try:
			self.SetInsertionPoint(1)   # Best of all worlds (really)
			self.SetSelection(-1,-1)    # select all text
		except AttributeError:
			# Only works for text controls
			pass


	def selectNone(self):
		""" Select no text in the control."""
		try:
			self.SetSelection(0,0)
		except AttributeError:
			# Only works for text controls
			pass


	def _coerceValue(self, val, oldval):
		convTypes = (str, unicode, int, float, long, complex)
		oldType = type(oldval)
		if isinstance(val, convTypes) and isinstance(oldval, basestring):
			if isinstance(oldType, str):
				val = str(val)
			else:
				if not isinstance(val, unicode):
					val = unicode(val, self.Application.Encoding)
		elif isinstance(oldval, int) and isinstance(val, basestring):
			if val:
				val = int(val)
			else:
				val = 0
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
			if type(self.Value) != type(val):
				val = self._coerceValue(val, self.Value)
			if (type(self.Value) != type(val) or self.Value != val):
				setter = self.SetValue
				if hasattr(self, "ChangeValue"):
					setter = self.ChangeValue
				try:
					setter(val)
				except TypeError, e:
					dabo.logError(_("Could not set value of %s to %s. Error message: %s")
							% (self._name, val, e))
			self.flushValue()
		else:
			self._properties["Value"] = val


	Value = property(_getValue, _setValue, None,
		_("""Specifies the current state of the control (the value of the
				field).  (varies)"""))


	DynamicValue = makeDynamicProperty(Value)

