import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _

class dRadioGroup(wx.RadioBox, dcm.dDataControlMixin):
	""" Allows choosing one option from a list of options.
	"""
	def __init__(self, parent, id=-1, label='', 
		choices=['Option A', 'Option B'], style=0, *args, **kwargs):

		self._baseClass = dRadioGroup
		name, _explicitName = self._processName(kwargs, "dRadioGroup")

		pre = wx.PreRadioBox()
		self._beforeInit(pre)                  # defined in dPemMixin

		try:	
			maxElements = pre._maxElements
		except AttributeError:
			maxElements = 1

		pre.Create(parent, id, label=label, choices=choices, majorDimension=maxElements,
				style=style|pre.GetWindowStyle(), *args, **kwargs)

		self.PostCreate(pre)

		dcm.dDataControlMixin.__init__(self, name, _explicitName=_explicitName)
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
			
	def _getElementEditorInfo(self):
		return {'editor': 'list', 'values': ['None', 'Row', 'Column']}
		
	def _setElement(self, val):
		val = str(val)
		self.delWindowStyleFlag(wx.RA_SPECIFY_ROWS)
		self.delWindowStyleFlag(wx.RA_SPECIFY_COLS)
		
		if val == "Row":
			self.addWindowStyleFlag(wx.RA_SPECIFY_ROWS)
		elif val == "Column":
			self.addWindowStyleFlag(wx.RA_SPECIFY_COLS)
		elif val == "None":
			pass
		else:
			raise ValueError, "The only possible settings are 'None', 'Row', and 'Column'."
			
	def _getValue(self):
		return self._pemObject.GetSelection()
	def _setValue(self, value):
		self._pemObject.SetSelection(int(value))

			
	# Property definitions:
	MaxElements = property(_getMaxElements, _setMaxElements, None,
						'Specifies the maximum rows, if Element=="Row", or the maximum columns, '
						'if Element=="Column". When the max is reached, the radio group will grow '
						'in the opposite direction to accomodate. Read-only at runtime. (int).')
	
	Element = property(_getElement, _setElement, None,
						'Specifies the direction that MaxElements is limited to. Read-only at runtime.\n'
						'	"None"\n'
						'	"Row"\n'
						'	"Column"')
	
	Value = property(_getValue, _setValue, None,
						'Specifies the current state of the control (the value of the field). (varies)')


if __name__ == "__main__":
	import test
	test.Test().runTest(dRadioGroup, choices=["apples", "mangoes"])
