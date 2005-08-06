from dabo.ui.dDataControlMixinBase import dDataControlMixinBase

class dDataControlMixin(dDataControlMixinBase):

	def select(self, position, length):
		""" Select all text from <position> for <length> or end of string.
		"""
		try:
			self.SetInsertionPoint(1)
			self.SetSelection(position, length)
		except AttributeError:
			# Only works for text controls
			pass
			
			
	def selectAll(self):
		""" Select all text in the control.
		"""
		try:	
			self.SetInsertionPoint(1)   # Best of all worlds (really)
			self.SetSelection(-1,-1)    # select all text
		except AttributeError:
			# Only works for text controls
			pass
			
			
	def selectNone(self):
		""" Select no text in the control.
		"""
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
				self.SetValue(value)
				self._afterValueChanged()
		else:
			self._properties["Value"] = value

		
	Value = property(_getValue, _setValue, None,
		'Specifies the current state of the control (the value of the field). (varies)')
