import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _

class dListBox(wx.ListBox, dcm.dDataControlMixin):
	""" Allows presenting a choice of items for the user to choose from.
	"""
	def __init__(self, parent, id=-1, choices=["Dabo", "Default"], 
			style=0, selectionType="single", properties=None, *args, **kwargs):

		self._baseClass = dListBox
		properties = self.extractKeywordProperties(kwargs, properties)
		name, _explicitName = self._processName(kwargs, self.__class__.__name__)

		pre = wx.PreListBox()
		self._beforeInit(pre)
		
		selType = selectionType.lower()[:1]
		if selType == "m":
			# multiple selections
			style = style | wx.LB_MULTIPLE
		elif selType in ("e", "d"):
			# 'extended' or 'discontinuous'
			style = style | wx.LB_EXTENDED
		
		style = style | pre.GetWindowStyle()
		
 		pre.Create(parent, id, choices=choices, style=style, *args, **kwargs)

		self.PostCreate(pre)

		# Determines if 'Value' is determined by position in 
		# the group, or the associated caption for the
		# selected button
		self._useStringValue = True
	
		dcm.dDataControlMixin.__init__(self, name, _explicitName=_explicitName)
		
		self.setProperties(properties)
		self._afterInit()


	def initEvents(self):
		#dListBox.doDefault()
		super(dListBox, self).initEvents()
		
		# catch the wx event and raise the dabo event:
		self.Bind(wx.EVT_LISTBOX, self._onWxHit)
		

	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getPosValue(self):
		return self._pemObject.GetSelection()
	def _setPosValue(self, value):
		self._pemObject.SetSelection(int(value))
	
	def _getStrValue(self):
		return self._pemObject.GetStringSelection()
	def _setStrValue(self, value):
		self._pemObject.SetStringSelection(str(value))

	def _getValue(self):
		if self._useStringValue:
			ret = self._getStrValue()
		else:
			ret = self._getPosValue()
		return ret
	def _setValue(self, value):
		if self._useStringValue:
			self._setStrValue(value)
		else:
			self._setPosValue(value)
	
	def _getUseStringValue(self):
		return self._useStringValue
	def _setUseStringValue(self, value):
		self._useStringValue = value

	
	# Property definitions:
	Value = property(_getValue, _setValue, None,
			"Specifies the current state of the control (the value of the field). (varies)")
	
	PositionValue = property(_getPosValue, _setPosValue, None,
			"Position of selected value (int)" )

	StringValue = property(_getStrValue, _setStrValue, None,
			"Text of selected value (str)" )

	UseStringValue = property(_getUseStringValue, _setUseStringValue, None,
			"Controls whether the Value of the control is the text/caption of "
			"the selection, or the position. (bool)")


if __name__ == "__main__":
	import test
	test.Test().runTest(dListBox, choices=["soccer", "basketball", "golf", "baseball"])

