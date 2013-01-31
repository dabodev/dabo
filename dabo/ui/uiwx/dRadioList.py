# -*- coding: utf-8 -*-
import sys
import time
import wx
import dabo
from dabo.ui import makeDynamicProperty
if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dControlItemMixin as cim
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class _dRadioButton(dcm.dDataControlMixin, wx.RadioButton):
	"""
	Subclass of wx.RadioButton. Not meant to be used individually, but
	only in the context of a parent dRadioList control.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = _dRadioButton
		preClass = wx.PreRadioButton
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)


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
			# These need to be handled by the parent dRadioList
			self.Bind(wx.EVT_SET_FOCUS, self.Parent._onButtonGotFocus)
			self.Bind(wx.EVT_KILL_FOCUS, self.Parent._onButtonLostFocus)

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


class dRadioList(cim.dControlItemMixin, wx.Panel):
	"""
	Creates a group of radio buttons, allowing mutually-exclusive choices.

	Like a dDropdownList, use this to present the user with multiple choices and
	for them to choose from one of the choices. Where the dDropdownList is
	suitable for lists of one to a couple hundred choices, a dRadioList is
	really only suitable for lists of one to a dozen at most.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dRadioList
		self._sizerClass = dabo.ui.dBorderSizer
		self._buttonClass = _dRadioButton
		self._showBox = True
		self._caption = ""
		preClass = wx.PrePanel
		style = self._extractKey((properties, attProperties, kwargs), "style", 0)
		style = style | wx.TAB_TRAVERSAL
		kwargs["style"] = style
		# Tracks individual member radio buttons.
		self._items = []
		self._selpos = 0
		# Tracks timing to determine whether any of the buttons
		# have changed focus so got/lost events can be raised
		self._lastGotFocusEvent = self._lastLostFocusEvent = 0
		# Default spacing between buttons. Can be changed with the
		# 'ButtonSpacing' property.
		self._buttonSpacing = 5

		cim.dControlItemMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)


	def _resetChoices(self):
		# Need to override as the base behavior calls undefined Clear() and AppendItems()
		pass


	def getBaseButtonClass(cls):
		return _dRadioButton
	getBaseButtonClass = classmethod(getBaseButtonClass)


	def _checkSizer(self):
		"""Makes sure the sizer is created before setting props that need it."""
		if self.Sizer is None:
			self.Sizer = self.SizerClass(self, orientation=self.Orientation, Caption=self.Caption)

	def _onWxHit(self, evt):
		pos = self._items.index(evt.GetEventObject())
		self.PositionValue = pos
		# This allows the event processing to properly
		# set the EventData["index"] properly.
		evt.SetInt(pos)
		self._userChanged = True
		super(dRadioList, self)._onWxHit(evt)


	def _onButtonGotFocus(self, wxEvt):
		# Received from individual buttons
		now = time.time()
		if now - self._lastLostFocusEvent > .01:
			# Newly focused; raise the event.
			# Missing uiEvent parameter in call? See note below.
			self.raiseEvent(dEvents.GotFocus)
		self._lastGotFocusEvent = now


	def _onButtonLostFocus(self, wxEvt):
		# Received from individual buttons
		now = time.time()
		self._lastLostFocusEvent = now

		@dabo.ui.deadCheck
		def checkForFocus(timeCalled):
			if timeCalled - self._lastGotFocusEvent > .01:
				# No other button has gotten focus in the intervening time
				# Don't raise event if parent form loses focus!
				# Doing it on Windows platform raises global Python exception.
				app = self.Application
				if app is None or app.ActiveForm == self.Form:
					# Passing wxEvt as uiEvent parameter under some conditions
					# causes Python interpreter crash or unspecified problems
					# with GC. I decided to remove this reference for both,
					# GotFocus and LostFocus event of control to retain symmetry.
					self.raiseEvent(dEvents.LostFocus)

		# Normal changing selection of buttons will cause buttons to lose focus;
		# we need to see if this control has truly lost focus.
		dabo.ui.callAfter(checkForFocus, now)


	def layout(self):
		"""Wrap the wx version of the call, if possible."""
		self.Layout()
		try:
			# Call the Dabo version, if present
			self.Sizer.layout()
		except AttributeError:
			pass
		if self.Application.Platform == "Win":
			self.refresh()


	def _setSelection(self, val):
		"""
		Set the selected state of the buttons to match this
		control's Value.
		"""
		for pos, itm in enumerate(self._items):
			itm.SetValue(pos == val)


	def enableKey(self, itm, val=True):
		"""Enables or disables an individual button, referenced by key value."""
		index = self.Keys[itm]
		self._items[index].Enabled = val


	def enablePosition(self, itm, val=True):
		"""Enables or disables an individual button, referenced by position (index)."""
		self._items[itm].Enabled = val


	def enableString(self, itm, val=True):
		"""Enables or disables an individual button, referenced by string display value."""
		mtch = [btn for btn in self.Children
				if isinstance(btn, _dRadioButton)
				and btn.Caption == itm]
		try:
			itm = mtch[0]
			idx = self._items.index(itm)
			self._items[idx].Enabled = val
		except IndexError:
			dabo.log.error(_("Could not find a button with Caption of '%s'") % itm)


	def enable(self, itm, val=True):
		"""
		Enables or disables an individual button.

		The itm argument specifies which button to enable/disable, and its type
		depends on the setting of self.ValueType:

			============ ====================
			"position"   The item is referenced by index position.
			"string"     The item is referenced by its string display value.
			"key"        The item is referenced by its key value.
			============ ====================

		"""
		if self.ValueMode == "position":
			self.enablePosition(itm, val)
		elif self.ValueMode == "string":
			self.enableString(itm, val)
		elif self.ValueMode == "key":
			self.enableKey(itm, val)


	def showKey(self, itm, val=True):
		"""Shows or hides an individual button, referenced by key value."""
		index = self.Keys[itm]
		self._items[index].Visible = val
		self.layout()


	def showPosition(self, itm, val=True):
		"""Shows or hides an individual button, referenced by position (index)."""
		self._items[itm].Visible = val
		self.layout()


	def showString(self, itm, val=True):
		"""Shows or hides an individual button, referenced by string display value."""
		mtch = [btn for btn in self._items if btn.Caption == itm]
		if mtch:
			mtch[0].Visible = val
		self.layout()


	def show(self, itm, val=True):
		"""
		Shows or hides an individual button.

		The itm argument specifies which button to hide/show, and its type
		depends on the setting of self.ValueType:

			============ ====================
			"position"   The item is referenced by index position.
			"string"     The item is referenced by its string display value.
			"key"        The item is referenced by its key value.
			============ ====================

		"""
		if self.ValueMode == "position":
			self.showPosition(itm, val)
		elif self.ValueMode == "string":
			self.showString(itm, val)
		elif self.ValueMode == "key":
			self.showKey(itm, val)


	def _getFudgedButtonSpacing(self):
		val = self._buttonSpacing
		if "linux" in sys.platform:
			# Buttons too widely spaced on Linux. Fudge it down...
			val -= 9
		val = (val, 0) if self.Orientation[:1].lower() == "h" else (0, val)
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
		if self._constructed():
			self._buttonSpacing = val
			self._checkSizer()
			sizer = self.Sizer
			spacing = self._getFudgedButtonSpacing()
			for itm in sizer.ChildSpacers:
				sizer.setItemProp(itm, "Spacing", spacing)
			self.layout()
		else:
			self._properties["ButtonSpacing"] = val


	def _getCaption(self):
		ret = self._caption
		if isinstance(self.Sizer, dabo.ui.dBorderSizer):
			ret = self._caption = self.Sizer.Caption
		return ret

	def _setCaption(self, val):
		if self._constructed():
			self._checkSizer()
			self._caption = val
			try:
				self.Sizer.Caption = val
			except AttributeError:
				pass
			try:
				self.Parent.layout()
			except AttributeError:
				self.layout()
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
			sv = (self.KeyValue, self.StringValue, self.PositionValue)
			[itm.release() for itm in self._items]
			self._choices = choices
			self._items = []
			self.Sizer.clear()
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
				# Try each saved value to restore which button is active:
				if self.Keys:
					self.KeyValue = sv[0]

				if not self.Keys or self.KeyValue != sv[0]:
					try:
						self.StringValue = sv[1]
					except ValueError:
						self.PositionValue = sv[2]
						if self.PositionValue != sv[2]:
							# Bail!
							self.PositionValue = 0
			else:
				self.PositionValue = 0

			self.layout()
		else:
			self._properties["Choices"] = choices


	def _getOrientation(self):
		return getattr(self, "_orientation", "Vertical")

	def _setOrientation(self, val):
		if self._constructed():
			self._checkSizer()
			if val[0].lower() not in "hv":
				val = "vertical"
			self._orientation = self.Sizer.Orientation = val
			# Reset button spacing also.
			self.ButtonSpacing = self.ButtonSpacing
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


	def _getShowBox(self):
		return self._showBox

	def _setShowBox(self, val):
		if self._constructed():
			fromSz = self.Sizer
			if fromSz is None:
				# Control hasn't been constructed yet
				dabo.ui.setAfter(self, "ShowBox", val)
				return
			self._showBox = val
			parent = fromSz.Parent
			isInSizer = fromSz.ControllingSizer is not None
			if isInSizer:
				csz = fromSz.ControllingSizer
				pos = fromSz.getPositionInSizer()
				szProps = csz.getItemProps(fromSz)
			isBorderSz = isinstance(fromSz, dabo.ui.dBorderSizer)
			needChange = (val and not isBorderSz) or (not val and isBorderSz)
			if not needChange:
				return
			if isBorderSz:
				toCls = fromSz.getNonBorderedClass()
				toSz = toCls()
			else:
				toCls = fromSz.getBorderedClass()
				toSz = toCls(parent)
				toSz.Caption = self._caption
			toSz.Orientation = fromSz.Orientation
			memberItems = fromSz.Children
			members = [fromSz.getItem(mem) for mem in memberItems]
			memberProps = dict.fromkeys(members)
			szProps = ("Border", "Proportion", "Expand", "HAlign", "VAlign", "BorderSides")
			for pos, member in enumerate(members):
				pd = {}
				for sp in szProps:
					pd[sp] = fromSz.getItemProp(memberItems[pos], sp)
				memberProps[member] = pd
			for member in members[::-1]:
				try:
					fromSz.remove(member)
				except AttributeError:
					# probably a spacer
					pass
			setSizer = (parent is not None) and (parent.Sizer is fromSz)
			if setSizer:
				parent.Sizer = None
			# Delete the old sizer.
			fromSz.release()
			if setSizer:
				parent.Sizer = toSz
			if isInSizer:
				itm = csz.insert(pos, toSz)
				csz.setItemProps(itm, szProps)
			for member in members:
				itm = toSz.append(member)
				toSz.setItemProps(itm, memberProps[member])
			try:
				self.Parent.layout()
			except AttributeError:
				self.layout()
		else:
			self._properties["ShowBox"] = val


	def _getSizerClass(self):
		return self._sizerClass

	def _setSizerClass(self, val):
		self._sizerClass = val


	def _getStringValue(self):
		try:
			ret = self._items[self._selpos].Caption
		except IndexError:
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
					raise ValueError, _("No radio button matching '%s' was found.") % val
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
			becomes the StringValue."""))

	Orientation = property(_getOrientation, _setOrientation, None,
			_("""Specifies whether this is a vertical or horizontal RadioList.
			String. Possible values:
				'Vertical' (the default)
				'Horizontal'"""))

	PositionValue = property(_getPositionValue, _setPositionValue, None,
			_("""Specifies the position (index) of the selected button.
			Integer. Read-write at runtime.
			Returns the current position, or sets the current position."""))

	ShowBox = property(_getShowBox, _setShowBox, None,
			_("Is the surrounding box visible?  (bool)"))

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
# 	def initProperties(self):
# 		self.ShowBox = False

	def afterInit(self):
		self.Caption = "Developers"
		self.BackColor = "lightyellow"
		developers = [{"lname": "McNett", "fname": "Paul", "iid": 42},
				{"lname": "Leafe", "fname": "Ed", "iid": 23},
				{"lname": "Roche", "fname": "Ted", "iid": 11}]

		self.Choices = ["%s %s" % (dev["fname"], dev["lname"]) for dev in developers]
		developers.append({"lname": "Hentzen", "fname": "Whil", "iid": 93})
		self.Choices = ["%s %s" % (dev["fname"], dev["lname"]) for dev in developers]
		keys = [dev["iid"] for dev in developers]
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
