import wx, dabo, dabo.ui
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlItemMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class dComboBox(wx.ComboBox, dcm.dControlItemMixin):
	"""Combination DropdownList and TextBox.
	
	The user can choose an item in the dropdown, or enter freeform text.
	"""
	_IsContainer = False
	isMultiSelect = False
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dComboBox
		self._choices = []
		self._keys = []
		self._invertedKeys = []
		self._valueMode = "string"
		self._userVal = False

		preClass = wx.PreComboBox
		dcm.dControlItemMixin.__init__(self, preClass, parent, properties, *args, **kwargs)


	def _initEvents(self):
		super(dComboBox, self)._initEvents()
		self.Bind(wx.EVT_COMBOBOX, self.__onComboBox)
		self.Bind(wx.EVT_TEXT_ENTER, self.__onTextBox)
			
	
	def __onComboBox(self, evt):
		self._userVal = False
		evt.Skip()
		self.raiseEvent(dabo.dEvents.Hit, evt)
		
		
	def __onTextBox(self, evt):
		self._userVal = True
		evt.Skip()
		self.raiseEvent(dabo.dEvents.Hit, evt)
	

	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getUserValue(self):
		if self._userVal:
			return self._pemObject.GetValue()
		else:
			return self._pemObject.GetStringSelection()
				
	def _setUserValue(self, value):
		self.SetValue(value)
		# don't call _afterValueChanged(), because value tracks the item in the list,
		# not the displayed value. User code can query UserValue and then decide to
		# add it to the list, if appropriate.
	
	UserValue = property(_getUserValue, _setUserValue, None,
		"""Specifies the text displayed in the textbox portion of the ComboBox.
		
		String. Read-write at runtime.
		
		UserValue can differ from StringValue, which would mean that the user
		has typed in arbitrary text. Unlike StringValue, PositionValue, and 
		KeyValue, setting UserValue does not change the currently selected item
		in the list portion of the ComboBox.
		""")

	

if __name__ == "__main__":
	import test
	
	class T(dComboBox):
		def afterInit(self):
			T.doDefault()
			self.BackColor = "aquamarine"
			self.ForeColor = "wheat"
			self.setup()
		
		def initEvents(self):
			T.doDefault()
			self.bindEvent(dabo.dEvents.Hit, self.onHit)
			
		def setup(self):
			print "Simulating a database:"
			developers = ({"lname": "McNett", "fname": "Paul", "iid": 42},
				{"lname": "Leafe", "fname": "Ed", "iid": 23})
			
			choices = []
			keys = {}
			for developer in developers:
				choices.append("%s %s" % (developer['fname'], developer['lname']))
				keys[developer["iid"]] = len(choices) - 1
			
			self.Choices = choices
			self.Keys = keys
			self.ValueMode = 'key'
			
		def onHit(self, evt):
			print "KeyValue: ", self.KeyValue
			print "PositionValue: ", self.PositionValue
			print "StringValue: ", self.StringValue
			print "Value: ", self.Value
			print "UserValue: ", self.UserValue
			
	test.Test().runTest(T)
