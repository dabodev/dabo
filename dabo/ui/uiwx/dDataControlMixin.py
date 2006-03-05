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
			

	def _getValue(self):
		return self.GetValue()
		
	def _setValue(self, value):
		if self._constructed():
			if (type(self.Value) != type(value) or self.Value != value):
				try:
					self.SetValue(value)
				except TypeError, e:
					dabo.errorLog.write(_("Could not set value of %s to %s. Error message: %s")
							% (self._name, value, e))
				self._afterValueChanged()
			else:
				# Call flushValue() anyway. Data binding properties may have
				# changed since the value was last set.
				self.flushValue()
		else:
			self._properties["Value"] = value

		
	Value = property(_getValue, _setValue, None,
		_("""Specifies the current state of the control (the value of the 
				field).  (varies)"""))
	DynamicValue = makeDynamicProperty(Value)

