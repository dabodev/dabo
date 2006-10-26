import wx
import dabo
import dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
from dabo.dLocalize import _
import dabo.dEvents as dEvents
from dabo.ui import makeDynamicProperty


class dButton(cm.dControlMixin, wx.Button):
	"""Creates a button that can be pressed by the user to trigger an action.

	Example:

	class MyButton(dabo.ui.dButton):
		def initProperties(self):
			self.Caption = "Press Me"

		def onHit(self, evt):
			self.Caption = "Press Me one more time"

	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dButton
		preClass = wx.PreButton
		cm.dControlMixin.__init__(self, preClass, parent, properties, 
				*args, **kwargs)


	def _initEvents(self):
		super(dButton, self)._initEvents()
		self.Bind(wx.EVT_BUTTON, self._onWxHit)
		
	
	def __onCancelButton(self, evt):
		# This callback exists for when the user presses ESC and this button
		# is the cancel button. Raise dEvents.Hit.
		self.raiseEvent(dEvents.Hit)


	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getCancelButton(self):
		try:
			return self.Parent._acceleratorTable["esc"] == self.__onCancelButton
		except KeyError:
			return False

	def _setCancelButton(self, val):
			## pkm: We can bind the key to self, Parent, or Form (or any object).
			##      If bound to self, the <esc> keypress will only fire the Hit
			##      when self has the focus. If bound to self.Parent, Hit will 
			##      fire when self.Parent or any of its children has the focus.
			##      If bound to self.Form, Hit will fire whenever <esc> is pressed.
			##      I'm making the decision to bind it to self.Form, even though
			##      self.Parent is also a valid choice.
			if val:
				self.Parent.bindKey("esc", self.__onCancelButton)
			else:
				self.Parent.unbindKey("esc")


	def _getDefaultButton(self):
		try:
			v = self._defaultButton
		except AttributeError:
			v = self._defaultButton = False
		return v

	def _setDefaultButton(self, value):
		if self._constructed():
			self._defaultButton = value
			if value:
				self.SetDefault()
				# Need to unset default from any other buttons:
				for child in self.Parent.Children:
					try:
						db = child.DefaultButton
					except:
						db = False
					if db:
						child.DefaultButton = False
			else:
				# No wx-way to unset default button. Probably a rare need, anyway.
				# One idea would be to create a hidden button, set default to it,
				# and then destroy it.
				pass
		else:
			self._properties["DefaultButton"] = value


	# Property definitions:
	CancelButton = property(_getCancelButton, _setCancelButton, None,
		_("Specifies whether this command button gets clicked on -Escape-."))
	DynamicCancelButton = makeDynamicProperty(CancelButton)
						
	DefaultButton = property(_getDefaultButton, _setDefaultButton, None, 
		_("Specifies whether this command button gets clicked on -Enter-."))
	DynamicDefaultButton = makeDynamicProperty(DefaultButton)

class _dButton_test(dButton):
	def initProperties(self):
		self.Caption = "You better not push me"
		self.FontSize = 8
		self.Width = 223

	def onContextMenu(self, evt):
		print "context menu"

	def onMouseRightClick(self, evt):
		print "right click"

	def onHit(self, evt):
		self.ForeColor = "purple"
		self.FontBold = True
		self.FontItalic = True
		self.Caption = "Ok, you cross this line, and you die."
		self.Width = 333

if __name__ == "__main__":
	import test
	test.Test().runTest(_dButton_test)
