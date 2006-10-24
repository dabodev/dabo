import sys
import wx
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dControlItemMixin as cim
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


class _dRadioButton(wx.RadioButton, dcm.dDataControlMixin):
	"""Subclass of wx.RadioButton. Not meant to be used individually, but
	only in the context of a parent dRadioList control.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = _dRadioButton
		preClass = wx.PreRadioButton
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
		

	def _initEvents(self):
		if isinstance(self.Parent, dRadioList):
			self.Bind(wx.EVT_RADIOBUTTON, self.Parent._onWxHit)
			# For some reason, these isn't happening via dPemMixin.
			self.Bind(wx.EVT_LEFT_DOWN, self.__onWxMouseLeftDown)
			self.Bind(wx.EVT_LEFT_UP, self.__onWxMouseLeftUp)
			self.Bind(wx.EVT_LEFT_DCLICK, self.__onWxMouseLeftDoubleClick)
			self.Bind(wx.EVT_RIGHT_DOWN, self.__onWxMouseRightDown)
			self.Bind(wx.EVT_RIGHT_UP, self.__onWxMouseRightUp)
			self.Bind(wx.EVT_RIGHT_DCLICK, self.__onWxMouseRightDoubleClick)
			self.Bind(wx.EVT_MIDDLE_DOWN, self.__onWxMouseMiddleDown)
			self.Bind(wx.EVT_MIDDLE_UP, self.__onWxMouseMiddleUp)
			self.Bind(wx.EVT_MIDDLE_DCLICK, self.__onWxMouseMiddleDoubleClick)
			self.Bind(wx.EVT_ENTER_WINDOW, self.__onWxMouseEnter)
			self.Bind(wx.EVT_LEAVE_WINDOW, self.__onWxMouseLeave)
			self.Bind(wx.EVT_MOTION, self.__onWxMouseMove)
			self.Bind(wx.EVT_MOUSEWHEEL, self.__onWxMouseWheel)
			self.Bind(wx.EVT_CONTEXT_MENU, self.__onWxContextMenu)
		
		if False:
			## Failed attempt to get arrow-key navigation of the buttons working on 
			## Gtk. The PositionValue changes but as soon as the Hit happens, the 
			## selection goes back to what it was before the keyboard navigation.
			self.bindKey("down", self._onArrow, arrowKey="down")
			self.bindKey("up", self._onArrow, arrowKey="up")
			self.bindKey("left", self._onArrow, arrowKey="left")
			self.bindKey("right", self._onArrow, arrowKey="right")


	def __onWxMouseLeftDown(self, evt):
		self.raiseEvent(dEvents.MouseLeftDown, evt)
	def __onWxMouseLeftUp(self, evt):
		self.raiseEvent(dEvents.MouseLeftUp, evt)
	def __onWxMouseLeftDoubleClick(self, evt):
		self.raiseEvent(dEvents.MouseLeftDoubleClick, evt)
	def __onWxMouseRightDown(self, evt):
		self.raiseEvent(dEvents.MouseRightDown, evt)
	def __onWxMouseRightUp(self, evt):
		self.raiseEvent(dEvents.MouseRightUp, evt)
	def __onWxMouseRightDoubleClick(self, evt):
		self.raiseEvent(dEvents.MouseRightDoubleClick, evt)
	def __onWxMouseMiddleDown(self, evt):
		self.raiseEvent(dEvents.MouseMiddleDown, evt)
	def __onWxMouseMiddleUp(self, evt):
		self.raiseEvent(dEvents.MouseMiddleUp, evt)
	def __onWxMouseMiddleDoubleClick(self, evt):
		self.raiseEvent(dEvents.MouseMiddleDoubleClick, evt)
	def __onWxMouseEnter(self, evt):
		self.raiseEvent(dEvents.MouseEnter, evt)
	def __onWxMouseLeave(self, evt):
		self.raiseEvent(dEvents.MouseLeave, evt)
	def __onWxMouseMove(self, evt):
		self.raiseEvent(dEvents.MouseMove, evt)
	def __onWxMouseWheel(self, evt):
		self.raiseEvent(dEvents.MouseWheel, evt)
	def __onWxContextMenu(self, evt):
		self.raiseEvent(dEvents.ContextMenu, evt)
	def __onWxMouseMove(self, evt):
		self.raiseEvent(dEvents.MouseMove, evt)
		

	def _onArrow(self, evt):
		## Failed attempt to get arrow-key navigation of the buttons working on Gtk.
		## This code will never be called, but I'll leave it in just in case I have
		## time to come back to it someday.
		arrowKey = evt.EventData["arrowKey"]
		if arrowKey in ("down", "right"):
			forward = True
		else:
			forward = False

		choiceCount = len(self.Parent.Choices)
		positionValue = self.Parent.PositionValue

		canMove = False
		while True:
			if forward:
				if choiceCount > (positionValue + 1):
					positionValue += 1
				else:
					break
			else:
				if positionValue > 0:
					positionValue -= 1
				else:
					break
			button = self.Parent._items[positionValue]
			if button.Visible and button.Enabled:
				canMove = True
				break
					
		if canMove:
			self.Parent.PositionValue = positionValue


class dRadioList(wx.Panel, cim.dControlItemMixin):
	"""Creates a group of radio buttons, allowing mutually-exclusive choices.

	Like a dDropdownList, use this to present the user with multiple choices and
	for them to choose from one of the choices. Where the dDropdownList is
	suitable for lists of one to a couple hundred choices, a dRadioList is 
	really only suitable for lists of one to a dozen at most.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dRadioList
		self._sizerClass = dabo.ui.dBorderSizer
		self._buttonClass = _dRadioButton
		preClass = wx.PrePanel
		style = self._extractKey((properties, kwargs), "style", 0)
		style = style | wx.TAB_TRAVERSAL
		kwargs["style"] = style
		# Tracks individual member radio buttons.
		self._items = []
		self._selpos = 0
		# Default spacing between buttons. Can be changed with the
		# 'ButtonSpacing' property.
		self._buttonSpacing = 5

		cim.dControlItemMixin.__init__(self, preClass, parent, properties, *args, **kwargs)


	def getBaseButtonClass(cls):
		return _dRadioButton
	getBaseButtonClass = classmethod(getBaseButtonClass)
	
	
	def _checkSizer(self):
		"""Makes sure the sizer is created before setting props that need it."""
		if self.Sizer is None:
			self.Sizer = self.SizerClass(self, orientation="v")

	
	def _onWxHit(self, evt):
		pos = self._items.index(evt.GetEventObject())
		self.PositionValue = pos
		# This allows the event processing to properly 
		# set the EventData["index"] properly.
		evt.SetInt(pos)
		self.flushValue()
		self.super(evt)
		
		
	def layout(self):
		""" Wrap the wx version of the call, if possible. """
		self.Layout()
		try:
			# Call the Dabo version, if present
			self.Sizer.layout()
		except:
			pass
		if self.Application.Platform == "Win":
			self.refresh()
	

	def _setSelection(self, val):
		"""Set the selected state of the buttons to match this
		control's Value.
		"""
		for pos, itm in enumerate(self._items):
			itm.SetValue(pos==val)
		

	def enableKey(self, item, val=True):
		"""Enables or disables an individual button, referenced by key value."""
		index = self.Keys[item]
		self._items[index].Enabled = val
	

	def enablePosition(self, item, val=True):
		"""Enables or disables an individual button, referenced by position (index)."""
		self._items[item].Enabled = val
		

	def enableString(self, item, val=True):
		"""Enables or disables an individual button, referenced by string display value."""
		index = self.FindString(item)
		self._items[index].Enabled = val
		

	def enable(self, item, val=True):
		"""Enables or disables an individual button.
		
		The item argument specifies which button to enable/disable, and its type
		depends on the setting of self.ValueType:		
			"position" : The item is referenced by index position.
			"string"   : The item is referenced by its string display value.
			"key"      : The item is referenced by its key value.
		"""
		if self.ValueMode == "position":
			self.enablePosition(item, val)
		elif self.ValueMode == "string":
			self.enableString(item, val)
		elif self.ValueMode == "key":
			self.enableKey(item, val)
		
		
	def showKey(self, item, val=True):
		"""Shows or hides an individual button, referenced by key value."""
		index = self.Keys[item]
		self._items[index].Visible = val
		self.layout()
		
	
	def showPosition(self, item, val=True):
		"""Shows or hides an individual button, referenced by position (index)."""
		self._items[item].Visible = val
		self.layout()
		
		
	def showString(self, item, val=True):
		"""Shows or hides an individual button, referenced by string display value."""
		mtch = [btn for btn in self._items if btn.Caption == item]
		if mtch:
			mtch[0].Visible = val
		self.layout()
		
		
	def show(self, item, val=True):
		"""Shows or hides an individual button.
		
		The item argument specifies which button to hide/show, and its type
		depends on the setting of self.ValueType:		
			"position" : The item is referenced by index position.
			"string"   : The item is referenced by its string display value.
			"key"      : The item is referenced by its key value.
		"""
		if self.ValueMode == "position":
			self.showPosition(item, val)
		elif self.ValueMode == "string":
			self.showString(item, val)
		elif self.ValueMode == "key":
			self.showKey(item, val)
		

	def _getFudgedButtonSpacing(self):
		val = self._buttonSpacing		
		if "linux" in sys.platform:
			# Buttons too widely spaced on Linux. Fudge it down...
			val -= 9
		return val


	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getButtonClass(self):
		return self._buttonClass

	def _setButtonClass(self, val):
		self._buttonClass = val


	def _getButtonSpacing(self):
		return self._buttonSpacing
		
	def _setButtonSpacing(self, val):
		self._buttonSpacing = val

		for itm in self.Sizer.ChildSpacers:
			self.Sizer.setItemProp(itm, "Spacing", self._getFudgedButtonSpacing())
		self.layout()
			
			
	def _getCaption(self):
		ret = ""
		if isinstance(self.Sizer, dabo.ui.dBorderSizer):
			ret = self.Sizer.Caption
		return ret
		
	def _setCaption(self, val):
		if self._constructed():
			self._checkSizer()
			self.Sizer.Caption = val
		else:
			self._properties["Caption"] = val


	def _getChoices(self):
		try:
			_choices = self._choices
		except AttributeError:
			_choices = self._choices = []
		return _choices
		
	def _setChoices(self, choices):
		if self._constructed():
			self._checkSizer()
			# Save the current values for possible re-setting afterwards.
			old_length = len(self.Choices)
			sv = (self.StringValue, self.KeyValue, self.PositionValue)
			[itm.release() for itm in self._items]
			self._choices = choices
			self._items = []
			for idx, itm in enumerate(choices):
				style = 0
				if idx == 0:
					if len(choices) == 1:
						style = wx.RB_SINGLE
					else:
						style = wx.RB_GROUP
				else:
					self.Sizer.appendSpacer(self._getFudgedButtonSpacing())
				btn = self.ButtonClass(self, Caption=itm, style=style)
				btn._index = idx
				self.Sizer.append(btn)
				self._items.append(btn)

			if old_length:
				# Try each saved value
				self.StringValue = sv[0]
				if self.StringValue != sv[0]:
					self.KeyValue = sv[1]
					if self.KeyValue != sv[1]:
						self.PositionValue = sv[2]
						if self.PositionValue != sv[2]:
							# Bail!
							self.PositionValue = 0
			else:
				self.PositionValue = 0

			self.layout()
		else:
			self._choices = self._properties["Choices"] = choices
	
	
	def _getOrientation(self):
		self._checkSizer()
		return self.Sizer.Orientation
	
	def _setOrientation(self, val):
		if self._constructed():
			self._checkSizer()
			self.Sizer.Orientation = val
			self.layout()
		else:
			self._properties["Orientation"] = val
			
		
	def _getPositionValue(self):
		return self._selpos
	
	def _setPositionValue(self, val):
		if self._constructed():
			self._selpos = val
			self._setSelection(val)
		else:
			self._properties["PositionValue"] = val


	def _getSizerClass(self):
		return self._sizerClass

	def _setSizerClass(self, val):
		self._sizerClass = val


	def _getStringValue(self):
		try:
			ret = self._items[self._selpos].Caption
		except:
			ret = None
		return ret
	
	def _setStringValue(self, val):
		if self._constructed():
			try:
				idx = [btn._index for btn in self._items if btn.Caption == val][0]
				self.PositionValue = idx
			except IndexError:
				if val is not None:
					# No such string.
					dabo.errorLog.write(_("No radio button matching '%s' was found.") % val)
		else:
			self._properties["StringValue"] = val
	
	
	# Property definitions:
	ButtonClass = property(_getButtonClass, _setButtonClass, None,
			_("Class to use for the radio buttons. Default=_dRadioButton  (dRadioButton)"))
	
	ButtonSpacing = property(_getButtonSpacing, _setButtonSpacing, None,
			_("Spacing in pixels between buttons in the control  (int)"))
			
	Caption = property(_getCaption, _setCaption, None,
			_("String to display on the box surrounding the control  (str)"))
	
	Choices = property(_getChoices, _setChoices, None,
			_("""Specifies the string choices to display in the list.
			-> List of strings. Read-write at runtime.
			The list index becomes the PositionValue, and the string 
			becomes the StringValue.""") )

	Orientation = property(_getOrientation, _setOrientation, None,
			_("""Specifies whether this is a vertical or horizontal RadioList.		
			String. Possible values:
				'None'
				'Row'
				'Column'"""))
				
	PositionValue = property(_getPositionValue, _setPositionValue, None,
			_("""Specifies the position (index) of the selected button.
			Integer. Read-write at runtime.
			Returns the current position, or sets the current position."""))

	SizerClass = property(_getSizerClass, _setSizerClass, None,
			_("Class to use for the border sizer. Default=dabo.ui.dBorderSizer  (dSizer)"))
	
	StringValue = property(_getStringValue, _setStringValue, None,
			_("""Specifies the text of the selected button.
			String. Read-write at runtime.		
			Returns the text of the current item, or changes the current position
			to the position with the specified text. An exception is raised if there
			is no position with matching text."""))


	DynamicOrientation = makeDynamicProperty(Orientation)
	DynamicPositionValue = makeDynamicProperty(PositionValue)
	DynamicStringValue = makeDynamicProperty(StringValue)

	

class _dRadioList_test(dRadioList):
	def afterInit(self):
		self.Caption = "Developers"
		self.BackColor = "lightyellow"
		developers = ({"lname": "McNett", "fname": "Paul", "iid": 42},
				{"lname": "Leafe", "fname": "Ed", "iid": 23},
				{"lname": "Roche", "fname": "Ted", "iid": 11})
			
		choices = ["%s %s" % (dev["fname"], dev["lname"]) for dev in developers]
		keys = [dev["iid"] for dev in developers]
		self.Choices = choices
		self.Keys = keys
		self.ValueMode = "key"

			
	def onHit(self, evt):
		print "KeyValue: ", self.KeyValue
		print "PositionValue: ", self.PositionValue
		print "StringValue: ", self.StringValue
		print "Value: ", self.Value

		

if __name__ == "__main__":
	import test
	test.Test().runTest(_dRadioList_test)
