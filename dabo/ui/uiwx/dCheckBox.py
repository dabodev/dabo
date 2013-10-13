# -*- coding: utf-8 -*-
import wx
import dabo
from dabo.ui import makeDynamicProperty
if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
from dabo.dLocalize import _


class dCheckBox(dcm.dDataControlMixin, wx.CheckBox):
	"""Creates a checkbox, allowing editing boolean values."""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dCheckBox
		preClass = wx.PreCheckBox
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)


	def _initEvents(self):
		super(dCheckBox, self)._initEvents()
		self.Bind(wx.EVT_CHECKBOX, self._onWxHit)


	def _initProperties(self):
		self._3StateToValue = { wx.CHK_UNCHECKED : False, wx.CHK_CHECKED : True, wx.CHK_UNDETERMINED : None}
		self._ValueTo3State = dict([[v,k] for k,v in self._3StateToValue.iteritems()])
		super(dCheckBox, self)._initProperties()


	def _getInitPropertiesList(self):
		additional = ["ThreeState", "Alignment"]
		original = list(super(dCheckBox, self)._getInitPropertiesList())
		return tuple(original + additional)


	def _onWxHit(self, evt):
		self._userChanged = True
		self.flushValue()
		super(dCheckBox, self)._onWxHit(evt)


	def getBlankValue(self):
		return False


	# property get/set functions
	def _getAlignment(self):
		if self._hasWindowStyleFlag(wx.ALIGN_RIGHT):
			return "Right"
		else:
			return "Left"

	def _setAlignment(self, val):
		self._delWindowStyleFlag(wx.ALIGN_RIGHT)
		if val.lower()[0] == "r":
			self._addWindowStyleFlag(wx.ALIGN_RIGHT)
		elif val.lower()[0] == "l":
			pass
		else:
			raise ValueError(_("The only possible values are 'Left' and 'Right'."))


	def _getThreeState(self):
		return self._hasWindowStyleFlag(wx.CHK_3STATE)

	def _setThreeState(self, val):
		self._delWindowStyleFlag(wx.CHK_3STATE)
		if val == True:
			self._addWindowStyleFlag(wx.CHK_3STATE)


	def _getUserThreeState(self):
		return self._hasWindowStyleFlag(wx.CHK_ALLOW_3RD_STATE_FOR_USER)

	def _setUserThreeState(self, val):
		self._delWindowStyleFlag(wx.CHK_ALLOW_3RD_STATE_FOR_USER)
		if val == True:
			self._addWindowStyleFlag(wx.CHK_ALLOW_3RD_STATE_FOR_USER)


	def _getValue(self):
		if not self._hasWindowStyleFlag(wx.CHK_3STATE):
			return dcm.dDataControlMixin._getValue(self)
		else:
			return self._3StateToValue.get(self.Get3StateValue(), None)

	def _setValue(self, val):
		if self._constructed():
			if not self._hasWindowStyleFlag(wx.CHK_3STATE):
				dcm.dDataControlMixin._setValue(self, val)
			else:
				try:
					state = self._ValueTo3State[val]
				except KeyError:
					state = False
				self.Set3StateValue(state)
		else:
			self._properties["Value"] = val


	# property definitions follow:
	Alignment = property(_getAlignment, _setAlignment, None,
			_("""Specifies the alignment of the text.

				Left  : Checkbox to left of text (default)
				Right : Checkbox to right of text"""))

	ThreeState = property(_getThreeState, _setThreeState, None,
			_("""Specifies wether the checkbox support 3 states.

				True  : Checkbox supports 3 states
				False : Checkbox supports 2 states (default)"""))

	UserThreeState = property(_getUserThreeState, _setUserThreeState, None,
			_("""Specifies whether the user is allowed to set the third state.

				True  : User is allowed to set the third state.
				False : User isn't allowed to set the third state.(default)"""))

	Value = property(_getValue, _setValue, None,
			_("Specifies the current state of the control (the value of the field). (varies)"))


	DynamicAlignment = makeDynamicProperty(Alignment)
	DynamicThreeState = makeDynamicProperty(ThreeState)
	DynamicUserThreeState = makeDynamicProperty(UserThreeState)
	DynamicValue = makeDynamicProperty(Value)



class _dCheckBox_test(dCheckBox):
	def initProperties(self):
		self.Caption = _("Do you wish to pass?")

class _dCheckBox_test3_a(dCheckBox):
	def initProperties(self):
		self.Caption = _("3-state / None; user 3-state:False")
		self.ThreeState = True
		self.Value = None

class _dCheckBox_test3_b(dCheckBox):
	def initProperties(self):
		self.Caption = _("3-state / None; user 3-state:True")
		self.ThreeState = True
		self.UserThreeState = True
		self.Value = None


if __name__ == "__main__":
	import test
	test.Test().runTest(
		(_dCheckBox_test, _dCheckBox_test3_a, _dCheckBox_test3_b))
