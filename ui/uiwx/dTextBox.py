import wx, dabo, dabo.ui
import types
if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
from dabo.dLocalize import _

class dTextBox(wx.TextCtrl, dcm.dDataControlMixin):
	""" Allows editing one line of string or unicode data.
	"""
	def __init__(self, parent, id=-1, password=False, style=0, *args, **kwargs):

		self._baseClass = dTextBox
		name, _explicitName = self._processName(kwargs, "dTextBox")

		# Handles different value types
		self.valueType = types.StringType
		
		# If this is a password textbox, update the style parameter
		if password:
			style = style | wx.TE_PASSWORD

		pre = wx.PreTextCtrl()
		self._beforeInit(pre)
		pre.Create(parent, id, style=style|pre.GetWindowStyleFlag(), *args, **kwargs)
		self.PostCreate(pre)

		dcm.dDataControlMixin.__init__(self, name, _explicitName=_explicitName)
		
		self._afterInit()

		
	def initProperties(self):
		#dTextBox.doDefault()
		super(dTextBox, self).initProperties()
		self.SelectOnEntry = True


	def initEvents(self):
		#dTextBox.doDefault()
		super(dTextBox, self).initEvents()
		# catch wx.EVT_TEXT and raise dEvents.Hit:
		self.Bind(wx.EVT_TEXT, self._onWxHit)
		
		
	# property get/set functions
	def _getAlignment(self):
		if self.hasWindowStyleFlag(wx.TE_RIGHT):
			return "Right"
		elif self.hasWindowStyleFlag(wx.TE_CENTRE):
			return "Center"
		else:
			return "Left"

	def _getAlignmentEditorInfo(self):
		return {'editor': 'list', 'values': ['Left', 'Center', 'Right']}

	def _setAlignment(self, value):
		# Note: alignment doesn't seem to work, at least on GTK2
		self.delWindowStyleFlag(wx.TE_LEFT)
		self.delWindowStyleFlag(wx.TE_CENTRE)
		self.delWindowStyleFlag(wx.TE_RIGHT)

		value = str(value)

		if value == 'Left':
			self.addWindowStyleFlag(wx.TE_LEFT)
		elif value == 'Center':
			self.addWindowStyleFlag(wx.TE_CENTRE)
		elif value == 'Right':
			self.addWindowStyleFlag(wx.TE_RIGHT)
		else:
			raise ValueError, "The only possible values are 'Left', 'Center', and 'Right'"

	def _getReadOnly(self):
		return not self._pemObject.IsEditable()
	def _setReadOnly(self, value):
		self._pemObject.SetEditable(not bool(value))

	def _getPasswordEntry(self):
		return self.hasWindowStyleFlag(wx.TE_PASSWORD)
	def _setPasswordEntry(self, value):
		self.delWindowStyleFlag(wx.TE_PASSWORD)
		if value:
			self.addWindowStyleFlag(wx.TE_PASSWORD)
		# Note: control needs to be recreated for this flag change
		#       to take effect.
	
	def _getSelectOnEntry(self):
		try:
			return self._SelectOnEntry
		except AttributeError:
			return False
	def _setSelectOnEntry(self, value):
		self._SelectOnEntry = bool(value)

	def _getValue(self):
		try:
			typ = self.valueType
			retVal = self.GetValue()
			if typ == types.BooleanType:
				if value == "True":
					retVal = True
				else:
					retVal = False
			elif typ== types.NoneType:
				retVal = None
			elif typ == types.FloatType:
				retVal = float(retVal)
			elif typ == types.IntType:
				retVal = int(retVal)
			elif typ == types.LongType:
				retVal = long(retVal)
			elif typ == types.UnicodeType:
				retVal = unicode(retVal)
				
		except StandardError, e:
			retVal = "ERROR"
			dabo.errorLog.write("getval: %s" % e)
			
		return retVal
		
	def _setValue(self, value):
		typ = type(value)
		self.valueType = typ
		strVal = value
		# Must convert all to string for display
		if typ == types.BooleanType:
			if value:
				strVal = "True"
			else:
				strVal = "False"
		elif typ == types.NoneType:
			strVal = "None"
		elif typ in (types.StringType, types.UnicodeType):
			strVal = value
		else:
			strVal = str(value)
		self.SetValue(strVal)

		
	# Property definitions:
	Value = property(_getValue, _setValue, None,
			"Specifies the current state of the control (the value of the field). (varies)")

	Alignment = property(_getAlignment, _setAlignment, None,
			"Specifies the alignment of the text. (str) \n"
			"   Left (default) \n"
			"   Center \n"
			"   Right")

	ReadOnly = property(_getReadOnly, _setReadOnly, None, 
			"Specifies whether or not the text can be edited. (bool)")

	PasswordEntry = property(_getPasswordEntry, _setPasswordEntry, None,
			"Specifies whether plain-text or asterisks are echoed. (bool)")
	
	SelectOnEntry = property(_getSelectOnEntry, _setSelectOnEntry, None, 
			"Specifies whether all text gets selected upon receiving focus. (bool)")


if __name__ == "__main__":
	import test
	test.Test().runTest(dTextBox)
