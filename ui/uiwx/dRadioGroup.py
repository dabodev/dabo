import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _

class dRadioGroup(wx.RadioBox, dcm.dDataControlMixin):
	""" Allows choosing one option from a list of options.
	"""
	def __init__(self, parent, id=-1, label="", maxElements=1, 
		orientation="col", choices=["Option A", "Option B"], 
		style=0, properties=None, *args, **kwargs):

		self._baseClass = dRadioGroup
		properties = self.extractKeywordProperties(kwargs, properties)
		name, _explicitName = self._processName(kwargs, self.__class__.__name__)

		pre = wx.PreRadioBox()
		self._beforeInit(pre)                  # defined in dPemMixin
		
		# Internal reference to the choices available
		self._choices = choices
		

		if orientation.lower() in ("col", "columns", "column", "vert", "v", "vertical"):
			style = style | wx.RA_SPECIFY_COLS
		else:
			style = style | wx.RA_SPECIFY_ROWS

		pre.Create(parent, id, label=label, choices=choices, majorDimension=maxElements,
				style=style|pre.GetWindowStyle(), *args, **kwargs)

		self.PostCreate(pre)

		# Determines if 'Value' is determined by position in 
		# the group, or the associated caption for the
		# selected button
		self._useStringValue = True
	
		dcm.dDataControlMixin.__init__(self, name, _explicitName=_explicitName)
		
		self.setProperties(properties)
		self._afterInit()                      # defined in dPemMixin


	def initEvents(self):
		#dRadioGroup.doDefault()
		super(dRadioGroup, self).initEvents()
		self.Bind(wx.EVT_RADIOBOX, self._onWxHit)
		
		
	def getPropertyInfo(self, name):
		#d = dRadioGroup.doDefault(name)
		d = super(dRadioGroup, self).getPropertyinfo(name)
		if not d['preInitProperty']:
			d['preInitProperty'] = name in ('MaxElements', 'Element', 'OptionList')
		return d
	
	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getMaxElements(self):
		try:
			return self._pemObject._maxElements
		except AttributeError:
			return 3
	def _setMaxElements(self, val):
		self._pemObject._maxElements = int(val)
		
	def _getElement(self):
		if self.hasWindowStyleFlag(wx.RA_SPECIFY_ROWS):
			return "Row"
		elif self.hasWindowStyleFlag(wx.RA_SPECIFY_COLS):
			return "Column"
		else:
			return "None"
	def _setElement(self, val):
		val = str(val).lower()
		self.delWindowStyleFlag(wx.RA_SPECIFY_ROWS)
		self.delWindowStyleFlag(wx.RA_SPECIFY_COLS)
		if val == "row":
			self.addWindowStyleFlag(wx.RA_SPECIFY_ROWS)
		elif val[:3] == "col":
			self.addWindowStyleFlag(wx.RA_SPECIFY_COLS)
		elif val == "none":
			pass
		else:
			raise ValueError, "The only possible settings are 'None', 'Row', and 'Column'."
			
			
	def _getElementEditorInfo(self):
		return {'editor': 'list', 'values': ['None', 'Row', 'Column']}
		
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

	def _getChoices(self):
		try:
			ret = self._choices
		except AttributeError:
			ret = self._choices = []
		return ret
	def _setChoices(self, choices):
		if choices == self._choices:
			# No change; don't bother
			return
		self._choices = choices
### This is all experimental. It doesn't seem to be possible to 
###  re-create the radio group on the fly.
# 		# Save current choice by position
# 		currVal = self._pemObject.GetSelection()
# 		newObj = self.reCreate()
# 		pos = 0
# 		childCount = self._pemObject.GetCount()
# 		self.Clear()
# 		self.AppendItems(choices)

		
		
	# Property definitions:
	Choices = property(_getChoices, None, None,
			"Specifies the list of choices available in the list. The number of choices "
			"cannot be increased at runtime, but the value of the choice can be changed.")	

	MaxElements = property(_getMaxElements, _setMaxElements, None,
			"Specifies the maximum rows, if Element=='Row', or the maximum columns, "
			"if Element=='Column'. When the max is reached, the radio group will grow "
			"in the opposite direction to accomodate. Read-only at runtime. (int).")
	
	Element = property(_getElement, _setElement, None,
			"Specifies the direction that MaxElements is limited to. Read-only at runtime.\n"
			"	'None'\n"
			"	'Row'\n"
			"	'Column'")

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
	test.Test().runTest(dRadioGroup, choices=["apples", "mangoes"])
