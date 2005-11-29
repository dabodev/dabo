import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _

	
class dCheckBox(wx.CheckBox, dcm.dDataControlMixin):
	"""Creates a checkbox, allowing editing boolean values.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dCheckBox
		preClass = wx.PreCheckBox
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

	
	def _initEvents(self):
		super(dCheckBox, self)._initEvents()
		self.Bind(wx.EVT_CHECKBOX, self._onWxHit)
	
	def initProperties(self):
		self._3StateToValue = { wx.CHK_UNCHECKED : False, wx.CHK_CHECKED : True, wx.CHK_UNDETERMINED : None}
		self._ValueTo3State = dict([[v,k] for k,v in self._3StateToValue.iteritems()])

	def _getInitPropertiesList(self):
		additional = ["ThreeState"]
		original = list(super(dCheckBox, self)._getInitPropertiesList())
		return tuple(original + additional)
			
	def _onWxHit(self, evt):
		self.flushValue()
		dCheckBox.doDefault(evt)

	
	# property get/set functions
	def _getValue(self):
		if not self._hasWindowStyleFlag(wx.CHK_3STATE):
			return dcm.dDataControlMixin._getValue(self)
		else:
			return self._3StateToValue[self.Get3StateValue()]
		
	def _setValue(self, value):
		if not self._hasWindowStyleFlag(wx.CHK_3STATE):
			dcm.dDataControlMixin._setValue(self, value)
		else:
			try:
				state = self._ValueTo3State[value]
			except:
				state = False

			self.Set3StateValue(state)

	def _getAlignment(self):
		if self._hasWindowStyleFlag(wx.ALIGN_RIGHT):
			return "Right"
		else:
			return "Left"

	def _setAlignment(self, value):
		self._delWindowStyleFlag(wx.ALIGN_RIGHT)
		if str(value) == "Right":
			self._addWindowStyleFlag(wx.ALIGN_RIGHT)
		elif str(value) == "Left":
			pass
		else:
			raise ValueError, "The only possible values are 'Left' and 'Right'."

	def _getThreeState(self):
		if self._hasWindowStyleFlag(wx.CHK_3STATE):
			return True
		else:
			return False

	def _setThreeState(self, value):
		self._delWindowStyleFlag(wx.CHK_3STATE)
		if value == True:
			self._addWindowStyleFlag(wx.CHK_3STATE)
		
	def _getUserThreeState(self):
		if self._hasWindowStyleFlag(wx.CHK_ALLOW_3RD_STATE_FOR_USER):
			return True
		else:
			return False

	def _setUserThreeState(self, value):
		self._delWindowStyleFlag(wx.CHK_ALLOW_3RD_STATE_FOR_USER)
		if value == True:
			self._addWindowStyleFlag(wx.CHK_ALLOW_3RD_STATE_FOR_USER)

	# property definitions follow:
	Alignment = property(_getAlignment, _setAlignment, None,
		"""Specifies the alignment of the text.
			
		Left  : Checkbox to left of text (default)
		Right : Checkbox to right of text
		""")

	ThreeState = property(_getThreeState, _setThreeState, None,
		"""Specifies wether the checkbox support 3 states.
			
		True  : Checkbox supports 3 states
		False : Checkbox supports 2 states (default)
		""")

	UserThreeState = property(_getUserThreeState, _setUserThreeState, None,
		"""Specifies whether the user is allowed to set the third state.
			
		True  : User is allowed to set the third state.
		False : User isn't allowed to set the third state.(default)
		""")

	Value = property(_getValue, _setValue, None,
		'Specifies the current state of the control (the value of the field). (varies)')

class _dCheckBox_test(dCheckBox):
			def initProperties(self):
				self.Caption = "Do you wish to pass?"
				self.Width = 222			

if __name__ == "__main__":
	import test
	test.Test().runTest(_dCheckBox_test)
