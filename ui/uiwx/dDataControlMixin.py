from dabo.ui.dDataControlMixinBase import dDataControlMixinBase

class dDataControlMixin(dDataControlMixinBase):
	
	def _getValue(self):
		return self.GetValue()
		
	def _setValue(self, value):
		self.SetValue(value)

		
	Value = property(_getValue, _setValue, None,
		'Specifies the current state of the control (the value of the field). (varies)')
