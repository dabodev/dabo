import wx, dabo
import dControlMixin as cm
import dDataControlMixin as dcm
import dEvents
from dabo.dLocalize import _

class dRadioGroup(wx.RadioBox, dcm.dDataControlMixin, cm.dControlMixin):
	""" Allows choosing one option from a list of options.
	"""
	def __init__(self, parent, id=-1, label='', name="dRadioGroup", style=0, *args, **kwargs):

		self._baseClass = dRadioGroup

		pre = wx.PreRadioBox()
		self._beforeInit(pre)                  # defined in dPemMixin
		
		try:
			choices = pre._optionList
		except AttributeError:
			choices = ['Option A', 'Option B']
		
		try:	
			maxElements = pre._maxElements
		except AttributeError:
			maxElements = 1

		pre.Create(parent, id, label=label, choices=choices, majorDimension=maxElements,
				name=name, style=style|pre.GetWindowStyle(), *args, **kwargs)

		self.PostCreate(pre)

		cm.dControlMixin.__init__(self, name)
		dcm.dDataControlMixin.__init__(self)
		self._afterInit()                      # defined in dPemMixin


	def initEvents(self):
		# init the common events:
		cm.dControlMixin.initEvents(self)
		dcm.dDataControlMixin.initEvents(self)

		# init the widget's specialized event(s):
		self.bindEvent(dEvents.RadioBox, self.onRadioBox)
		self.bindEvent(dEvents.RadioBox, self._onRadioBox)

	# Event callback method(s) (override in subclasses):
	def onRadioBox(self, event):
		if self.debug:
			dabo.infoLog.write("onRadioBox received by %s" % self.Name)
		event.Skip()

	# Private Event callback method(s) (do not override):
	def _onRadioBox(self, event):
		self.raiseEvent(dEvents.ValueChanged)
		event.Skip()

	def getPropertyInfo(self, name):
		d = dRadioGroup.doDefault(name)
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
			
	def _getOptionList(self):
		l = []
		for item in range(self._pemObject.GetCount()):
			l.append(self._pemObject.GetString(item))
		return l
	
	def _getOptionListEditorInfo(self):
		return {'editor': 'propvallist'}
			
	def _setOptionList(self, val):
		if type(val) == type(list()):
			self._pemObject._optionList = val
		else:
			raise TypeError, "Option list must be a Python list."
			
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
	
	OptionList = property(_getOptionList, _setOptionList, None,
						'Specifies the list of options to display. Read-only at runtime. (list of strings).')
	
	Value = property(_getValue, _setValue, None,
						'Specifies the current state of the control (the value of the field). (varies)')


if __name__ == "__main__":
	import test
	test.Test().runTest(dRadioBox)
