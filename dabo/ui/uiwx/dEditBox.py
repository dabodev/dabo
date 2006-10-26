import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


# The EditBox is just a TextBox with some additional styles.

class dEditBox(dcm.dDataControlMixin, wx.TextCtrl):
	"""Creates an editbox, which allows editing of string data of unlimited size.

	The editbox will create scrollbars as necessary, and can edit string or 
	unicode data.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dEditBox
		self._forceCase = None
		self._inForceCase = False
		preClass = wx.PreTextCtrl
		kwargs["style"] = wx.TE_MULTILINE | wx.TE_WORDWRAP
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)


	def _initEvents(self):
		super(dEditBox, self)._initEvents()
		self.Bind(wx.EVT_TEXT, self._onWxHit)
		

	def selectAll(self):
		"""Each subclass must define their own selectAll method. This will 
		be called if SelectOnEntry is True when the control gets focus.
		"""
		self.SetSelection(-1, -1)
		
		
	def getBlankValue(self):
		return ""
	
	
	def scrollToBeginning(self):
		"""Moves the insertion point to the beginning of the text"""
		self.SetInsertionPoint(0)
		

	def scrollToEnd(self):
		"""Moves the insertion point to the end of the text"""
		self.SetInsertionPointEnd()
		

	def __onKeyChar(self, evt):
		"""This handles KeyChar events when ForceCase is set to a non-empty value."""
		keyChar = evt.keyChar
		if keyChar is not None and (keyChar.isalnum() 
				or keyChar in """,./<>?;':"[]\\{}|`~!@#$%%^&*()-_=+"""):
			dabo.ui.callAfter(self.__forceCase)
		
	
	def __forceCase(self):
		"""If the ForceCase property is set, casts the current value of the control
		to the specified case.
		"""
		if not isinstance(self.Value, basestring):
			# Don't bother if it isn't a string type
			return
		case = self.ForceCase
		if not case:
			return
		insPos = self.InsertionPosition
		selLen = self.SelectionLength
		changed = False
		self._inForceCase = True
		if case == "upper":
			self.Value = self.Value.upper()
			changed = True
		elif case == "lower":
			self.Value = self.Value.lower()
			changed = True
		elif case == "title":
			self.Value = self.Value.title()
			changed = True
		if changed:
			#self.SelectionStart = selStart
			self.InsertionPosition = insPos
			self.SelectionLength = selLen
			self.refresh()
		self._inForceCase = False
		

	# property get/set functions
	def _getAlignment(self):
		if self._hasWindowStyleFlag(wx.TE_RIGHT):
			return "Right"
		elif self._hasWindowStyleFlag(wx.TE_CENTRE):
			return "Center"
		else:
			return "Left"

	def _setAlignment(self, val):
		# Note: alignment doesn't seem to work, at least on GTK2
		self._delWindowStyleFlag(wx.TE_LEFT)
		self._delWindowStyleFlag(wx.TE_CENTRE)
		self._delWindowStyleFlag(wx.TE_RIGHT)
		val = val[0].lower()
		if val == "l":
			self._addWindowStyleFlag(wx.TE_LEFT)
		elif val == "c":
			self._addWindowStyleFlag(wx.TE_CENTRE)
		elif val == "r":
			self._addWindowStyleFlag(wx.TE_RIGHT)
		else:
			raise ValueError, _("The only possible values are 'Left', 'Center', and 'Right'")


	def _getForceCase(self):
		return self._forceCase

	def _setForceCase(self, val):
		if self._constructed():
			valKey = val[0].upper()
			self._forceCase = {"U": "upper", "L": "lower", "T": "title"}.get(valKey)
			self.__forceCase()
			self.unbindEvent(dEvents.KeyChar, self.__onKeyChar)
			if self._forceCase:
				self.bindEvent(dEvents.KeyChar, self.__onKeyChar)
		else:
			self._properties["ForceCase"] = val


	def _getInsertionPosition(self):
		return self.GetInsertionPoint()

	def _setInsertionPosition(self, val):
		self.SetInsertionPoint(val)


	def _getReadOnly(self):
		return not self.IsEditable()

	def _setReadOnly(self, value):
		if self._constructed():
			self.SetEditable(not value)
		else:
			self._properties["ReadOnly"] = value
	

	def _getSelectedText(self):
		return self.GetStringSelection()


	def _getSelectionEnd(self):
		return self.GetSelection()[1]

	def _setSelectionEnd(self, val):
		start, end = self.GetSelection()
		self.SetSelection(start, val)
		self.refresh()


	def _getSelectionLength(self):
		start, end = self.GetSelection()
		return end - start

	def _setSelectionLength(self, val):
		start = self.GetSelection()[0]
		self.SetSelection(start, start + val)
		self.refresh()


	def _getSelectionStart(self):
		return self.GetSelection()[0]

	def _setSelectionStart(self, val):
		start, end = self.GetSelection()
		self.SetSelection(val, end)
		self.refresh()


	def _getSelectOnEntry(self):
		try:
			return self._SelectOnEntry
		except AttributeError:
			return False
	def _setSelectOnEntry(self, value):
		self._SelectOnEntry = bool(value)
		

	def _getValue(self):
		return super(dEditBox, self)._getValue()
	
	def _setValue(self, val):
		if self._constructed():
			if self._inForceCase:
				# Value is changing internally. Don't update the oldval
				# setting or change the type; just set the value.
				self.SetValue(val)
				return
			else:
				ret = super(dEditBox, self)._setValue(val)
				self.__forceCase()
				return ret
		else:
			self._properties["Value"] = val

		
	# property definitions follow:
	Alignment = property(_getAlignment, _setAlignment, None,
			_("""Specifies the alignment of the text. (str)
			   Left (default)
			   Center
			   Right"""))

	ForceCase = property(_getForceCase, _setForceCase, None,
			_("""Determines if we change the case of entered text. Possible values are:
				None, "" (empty string): No changes made (default)
				"Upper": FORCE TO UPPER CASE
				"Lower": force to lower case
				"Title": Force To Title Case
			These can be abbreviated to "u", "l" or "t"  (str)"""))
	
	InsertionPosition = property(_getInsertionPosition, _setInsertionPosition, None,
			_("Position of the insertion point within the control  (int)"))
	
	ReadOnly = property(_getReadOnly, _setReadOnly, None, 
			_("Specifies whether or not the text can be edited. (bool)"))
	
	SelectedText = property(_getSelectedText, None, None,
			_("Currently selected text. Returns the empty string if nothing is selected  (str)"))	
	
	SelectionEnd = property(_getSelectionEnd, _setSelectionEnd, None,
			_("""Position of the end of the selected text. If no text is
			selected, returns the Position of the insertion cursor.  (int)"""))
	
	SelectionLength = property(_getSelectionLength, _setSelectionLength, None,
			_("Length of the selected text, or 0 if nothing is selected.  (int)"))
	
	SelectionStart = property(_getSelectionStart, _setSelectionStart, None,
			_("""Position of the beginning of the selected text. If no text is
			selected, returns the Position of the insertion cursor.  (int)"""))
	
	SelectOnEntry = property(_getSelectOnEntry, _setSelectOnEntry, None, 
			_("Specifies whether all text gets selected upon receiving focus. (bool)"))

	Value = property(_getValue, _setValue, None,
			_("Specifies the current state of the control (the value of the field). (varies)"))


	DynamicAlignment = makeDynamicProperty(Alignment)
	DynamicInsertionPosition = makeDynamicProperty(InsertionPosition)
	DynamicReadOnly = makeDynamicProperty(ReadOnly)
	DynamicSelectionEnd = makeDynamicProperty(SelectionEnd)
	DynamicSelectionLength = makeDynamicProperty(SelectionLength)
	DynamicSelectionStart = makeDynamicProperty(SelectionStart)
	DynamicSelectOnEntry = makeDynamicProperty(SelectOnEntry)
	DynamicValue = makeDynamicProperty(Value)



class _dEditBox_test(dEditBox):
	def initProperties(self):
		self.Size = (333, 175)
		self.Value = """Love, exciting and new
Come aboard, were expecting you
Love, lifes sweetest reward
Let it flow, it floats back to you

Love Boat soon will be making another run
The Love Boat promises something for everyone
Set a course for adventure
Your mind on a new romance

Love wont hurt anymore
Its an open smile on a friendly shore
Yes love...
Its love...

Love Boat soon will be making another run
The Love Boat promises something for everyone
Set a course for adventure
Your mind on a new romance

Love wont hurt anymore
Its an open smile on a friendly shore
Its love...
Its love...
Its love...
Its the Love Boat
Its the Love Boat 
"""
		
		self.ForceCase = "u"


if __name__ == "__main__":
	import test
	test.Test().runTest(_dEditBox_test)
