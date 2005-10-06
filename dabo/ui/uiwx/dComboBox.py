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
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dComboBox
		self._choices = []
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
			return self.GetValue()
		else:
			return self.GetStringSelection()
				
	def _setUserValue(self, value):
		if self._constructed():
			self.SetValue(value)
			# don't call _afterValueChanged(), because value tracks the item in the list,
			# not the displayed value. User code can query UserValue and then decide to
			# add it to the list, if appropriate.
		else:
			self._properties["UserValue"] = value
	
	UserValue = property(_getUserValue, _setUserValue, None,
		"""Specifies the text displayed in the textbox portion of the ComboBox.
		
		String. Read-write at runtime.
		
		UserValue can differ from StringValue, which would mean that the user
		has typed in arbitrary text. Unlike StringValue, PositionValue, and 
		KeyValue, setting UserValue does not change the currently selected item
		in the list portion of the ComboBox.
		""")


class _dComboBox_test(dComboBox):
	def initProperties(self):
		self.setup()
		self.Width = 300
		
	def initEvents(self):
		self.autoBindEvents()
			
	def setup(self):
		# Simulating a database:
		wannabeCowboys = ({"lname": "Reagan", "fname": "Ronald", "iid": 42},
			{"lname": "Bush", "fname": "George W.", "iid": 23})
			
		choices = []
		keys = {}
		for wannabe in wannabeCowboys:
			choices.append("%s %s" % (wannabe['fname'], wannabe['lname']))
			keys[wannabe["iid"]] = len(choices) - 1
			
		self.Choices = choices
		self.Keys = keys
		self.ValueMode = 'key'
			
	def onHit(self, evt):
		print "KeyValue: ", self.KeyValue
		print "PositionValue: ", self.PositionValue
		print "StringValue: ", self.StringValue
		print "Value: ", self.Value
		print "UserValue: ", self.UserValue
			


if __name__ == "__main__":
	import test
	test.Test().runTest(_dComboBox_test)
