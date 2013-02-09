# -*- coding: utf-8 -*-
import wx, dabo, dabo.ui
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlItemMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty
import dKeys


class dComboBox(dcm.dControlItemMixin, wx.ComboBox):
	"""
	Creates a combobox, which combines a dropdown list with a textbox.

	The user can choose an item in the dropdown, or enter freeform text.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dComboBox
		self._choices = []
		self._userVal = False
		# Used to force the case of entered text
		self._forceCase = None
		self._inForceCase = False
		self._textLength = None
		# Flag for appending items when the user presses 'Enter'
		self._appendOnEnter = False
		# Holds the text to be appended
		self._textToAppend = ""

		preClass = wx.PreComboBox
		dcm.dControlItemMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)


	def _preInitUI(self, kwargs):
		style = kwargs.get("style", 0)
		style |= wx.PROCESS_ENTER
		kwargs["style"] = style
		return kwargs


	def _initEvents(self):
		super(dComboBox, self)._initEvents()
		self.Bind(wx.EVT_COMBOBOX, self.__onComboBox)
# 		self.Bind(wx.EVT_TEXT_ENTER, self.__onTextBox)
		self.Bind(wx.EVT_KEY_DOWN, self.__onWxKeyDown)


	def __onComboBox(self, evt):
		self._userVal = False
		evt.Skip()
		self._onWxHit(evt)


	def __onWxKeyDown(self, evt):
		"""
		We need to capture the Enter/Return key in order to implement
		the AppendOnEnter behavior. However, under Windows this leads to
		navigation issues, so we also need to capture when Tab is pressed,
		and handle the navigation ourselves.
		"""
		# Shorthand for easy reference
		dk = dabo.ui.dKeys
		# Don't call the native Skip() if Tab is pressed; we'll handle it ourselves.
		callSkip = True
		enter_codes = (dk.key_Return, dk.key_Numpad_enter)
		keyCode = evt.GetKeyCode()
		if keyCode in enter_codes:
			self._userVal = True
			if self.AppendOnEnter:
				txt = self.GetValue()
				if txt not in self.Choices:
					self._textToAppend = txt
					if self.beforeAppendOnEnter() is not False:
						if self._textToAppend:
							self.appendItem(self._textToAppend, select=True)
							self.afterAppendOnEnter()
			self.raiseEvent(dEvents.Hit, evt)
		elif keyCode == dk.key_Tab:
			forward = not evt.ShiftDown()
			self.Navigate(forward)
			callSkip = False
		if callSkip:
			evt.Skip()


	def __onKeyChar(self, evt):
		"""This handles KeyChar events when ForceCase is set to a non-empty value."""
		if not self:
			# The control is being destroyed
			return
		keyCode = evt.keyCode
		if keyCode >= dKeys.key_Space:
			dabo.ui.callAfter(self._checkForceCase)
			dabo.ui.callAfter(self._checkTextLength)


	def _checkTextLength(self):
		"""
		If the TextLength property is set, checks the current value of the control
		and truncates it if too long
		"""
		if not self:
			# The control is being destroyed
			return
		if not isinstance(self.GetValue(), basestring):
			#Don't bother if it isn't a string type
			return
		length = self.TextLength
		if not length:
			return
		val = self.GetValue()
		if len(val) > length:
			dabo.ui.beep()
			ip = self.GetInsertionPoint()
			self.SetValue(val[:length])
			self.SetInsertionPoint(ip)


	def _checkForceCase(self):
		"""
		If the ForceCase property is set, casts the current value of the control
		to the specified case.
		"""
		if not self:
			# The control is being destroyed
			return
		if not isinstance(self.GetValue(), basestring):
			# Don't bother if it isn't a string type
			return
		case = self.ForceCase
		if not case:
			return
		ip = self.GetInsertionPoint()
		if case == "upper":
			self.SetValue(self.GetValue().upper())
		elif case == "lower":
			self.SetValue(self.GetValue().lower())
		elif case == "title":
			self.SetValue(self.GetValue().title())
		self.SetInsertionPoint(ip)


	def beforeAppendOnEnter(self):
		"""
		Hook method that is called when user-defined text is entered
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
		"""
		Hook method that provides a means to interact with the newly-
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


	def _getForceCase(self):
		return self._forceCase

	def _setForceCase(self, val):
		if self._constructed():
			if val is None:
				valKey = None
			else:
				valKey = val[0].upper()
			self._forceCase = {"U": "upper", "L": "lower", "T": "title", None: None,
					"None": None}.get(valKey)
			self._checkForceCase()
			self.unbindEvent(dEvents.KeyChar, self.__onKeyChar)
			if self._forceCase or self._textLength:
				self.bindEvent(dEvents.KeyChar, self.__onKeyChar)
		else:
			self._properties["ForceCase"] = val


	def _getTextLength(self):
		return self._textLength

	def _setTextLength(self, val):
		if self._constructed():
			if val == None:
				self._textLength = None
			else:
				val = int(val)
				if val < 1:
					raise ValueError('TextLength must be a positve Integer')
				self._textLength = val
			self._checkTextLength()

			self.unbindEvent(dEvents.KeyChar, self.__onKeyChar)
			if self._forceCase or self._textLength:
				self.bindEvent(dEvents.KeyChar, self.__onKeyChar)
		else:
			self._properties["TextLength"] = val


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

	ForceCase = property(_getForceCase, _setForceCase, None,
			_("""Determines if we change the case of entered text. Possible values are:

				============ =====================
				None or ""   No changes made (default)
				"Upper"      FORCE TO UPPER CASE
				"Lower"      Force to lower case
				"Title"      Force To Title Case
				============ =====================

			These can be abbreviated to "u", "l" or "t"  (str)"""))

	TextLength = property(_getTextLength, _setTextLength, None,
			_("""The maximum length the entered text can be. (int)"""))

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
			print _("Attempted to add Dabo to the list!!!")
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
