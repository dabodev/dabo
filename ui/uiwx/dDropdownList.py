import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _

class dDropdownList(wx.Choice, dcm.dDataControlMixin):
	""" Allows presenting a choice of items for the user to choose from.
	"""
	def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, 
			choices=["Dabo", "Default"], style=0, properties=None, *args, **kwargs):

		self._baseClass = dDropdownList
		properties = self.extractKeywordProperties(kwargs, properties)
		name, _explicitName = self._processName(kwargs, self.__class__.__name__)

		self._choices = list(choices)

		pre = wx.PreChoice()
		self._beforeInit(pre)
		style=style|pre.GetWindowStyle()
		pre.Create(parent, id, pos, size, choices, *args, **kwargs)

		self.PostCreate(pre)

		dcm.dDataControlMixin.__init__(self, name, _explicitName=_explicitName)
		
		self.setProperties(properties)
		self._afterInit()
		

	def initEvents(self):
		#dDropdownList.doDefault()
		super(dDropdownList, self).initEvents()
		
		# catch the wx event and raise the dabo event:
		self.Bind(wx.EVT_CHOICE, self._onWxHit)
		
	def _onWxHit(self, evt):
		super(dDropdownList, self)._onWxHit(evt)
		self._oldVal = self.Value
		
	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getChoices(self):
		try:
			_choices = self._choices
		except AttributeError:
			_choices = self._choices = []
		return _choices
		
	def _setChoices(self, choices):
#- 		if len(choices) != len(self.Choices):
#- 			raise ValueError, "Cannot change the length of the choices list."
		for index in range(len(choices)):
			self.SetString(index, choices[index])
		self._choices = choices
			
	def _getValue(self):
		s = self.GetStringSelection()
		return s
		
	def _setValue(self, value):
		try:
			self.SetStringSelection(value)
		except:
			raise ValueError, "Value must be present in the choices. (%s:%s)" % (
				value, self.Choices)
		self._oldVal = self.GetStringSelection()
		
	# Property definitions:
	Choices = property(_getChoices, _setChoices, None,
		"Specifies the list of choices available in the list. The number of choices "
		"cannot be changed at runtime, but the value of the choice can be changed.")	
	Value = property(_getValue, _setValue, None,
		"Specifies the current state of the control (the value of the field). (varies)")

if __name__ == "__main__":
	import test
	test.Test().runTest(dDropdownList)
