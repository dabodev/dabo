# -*- coding: utf-8 -*-
import wx, dabo, dabo.ui
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlItemMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


class dComboBox(dcm.dControlItemMixin, wx.ComboBox):
	"""Creates a combobox, which combines a dropdown list with a textbox.
	
	The user can choose an item in the dropdown, or enter freeform text.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dComboBox
		self._choices = []
		self._userVal = False
		# Flag for appending items when the user presses 'Enter'
		self._appendOnEnter = False
		# Holds the text to be appended
		self._textToAppend = ""

		preClass = wx.PreComboBox
		dcm.dControlItemMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)


	def _initEvents(self):
		super(dComboBox, self)._initEvents()
		self.Bind(wx.EVT_COMBOBOX, self.__onComboBox)
		self.Bind(wx.EVT_TEXT_ENTER, self.__onTextBox)
			
	
	def __onComboBox(self, evt):
		self._userVal = False
		evt.Skip()
		self._onWxHit(evt)
		
		
	def __onTextBox(self, evt):
		self._userVal = True
		evt.Skip()
		if self.AppendOnEnter:
			txt = evt.GetString()
			if txt not in self.Choices:
				self._textToAppend = txt
				if self.beforeAppendOnEnter() is not False:
					if self._textToAppend:
						self.appendItem(self._textToAppend, select=True)
						self.afterAppendOnEnter()
		self.raiseEvent(dabo.dEvents.Hit, evt)
	

	def beforeAppendOnEnter(self):
		"""Hook method that is called when user-defined text is entered
		into the combo box and Enter is pressed (when self.AppendOnEnter
		is True). This gives the programmer the ability to interact with such
		events, and optionally prevent them from happening. Returning 
		False will prevent the append from happening.
		
		The text value to be appended is stored in self._textToAppend. You
		may modify this value (e.g., force to upper case), or delete it entirely
		(e.g., filter out obscenities and such). If you set self._textToAppend
		to an empty string, nothing will be appended. So this 'before' hook
		gives you two opportunities to prevent the append: return a non-
		empty value, or clear out self._textToAppend.
		"""
		pass
		
		
	def afterAppendOnEnter(self):
		"""Hook method that provides a means to interact with the newly-
		changed list of items after a new item has been added by the user 
		pressing Enter, but before control returns to the program.
		"""
		pass
		
		
	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getAppendOnEnter(self):
		return self._appendOnEnter

	def _setAppendOnEnter(self, val):
		if self._constructed():
			self._appendOnEnter = val
		else:
			self._properties["AppendOnEnter"] = val


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
	
	
	AppendOnEnter = property(_getAppendOnEnter, _setAppendOnEnter, None,
			_("""Flag to determine if user-entered text is appended when they 
			press 'Enter'  (bool)"""))
	
	UserValue = property(_getUserValue, _setUserValue, None,
			_("""Specifies the text displayed in the textbox portion of the ComboBox.
			
			String. Read-write at runtime.
			
			UserValue can differ from StringValue, which would mean that the user
			has typed in arbitrary text. Unlike StringValue, PositionValue, and 
			KeyValue, setting UserValue does not change the currently selected item
			in the list portion of the ComboBox."""))
		
		
	DynamicUserValue = makeDynamicProperty(UserValue)



class _dComboBox_test(dComboBox):
	def initProperties(self):
		self.setup()
		self.AppendOnEnter = True
		
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
	
	
	def beforeAppendOnEnter(self):
		txt = self._textToAppend.strip().lower()
		if txt == "dabo":
			dabo.infoLog.write("Attempted to add Dabo to the list!!!")
			return False
		elif txt.find("nixon") > -1:
			self._textToAppend = "Tricky Dick"
		
		
	def onHit(self, evt):
		print "KeyValue: ", self.KeyValue
		print "PositionValue: ", self.PositionValue
		print "StringValue: ", self.StringValue
		print "Value: ", self.Value
		print "UserValue: ", self.UserValue
		
			
if __name__ == "__main__":
	import test
	test.Test().runTest(_dComboBox_test)
