import wx
import dabo
import dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
from dabo.dLocalize import _
import dabo.dEvents as dEvents

class dButton(wx.Button, cm.dControlMixin):
	""" Allows the user to cause an action to occur by pushing a button.
	"""
	_IsContainer = False
	
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
				self.Form.bindKey("esc", self.__onCancelButton)
			else:
				self.Form.unbindKey("esc")


	def _getDefaultButton(self):
		return self.Parent.GetDefaultItem() == self

	def _setDefaultButton(self, value):
		## pkm 2/9/2005: I'm tempted to reimplement the defaultbutton to use
		##               key bindings instead of wx's GetDefaultItem(), as that
		##               doesn't seem to work, at least not on all platforms.
		if value:
			self.Parent.SetDefaultItem(self)
		else:
			if self._pemObject.GetParent().GetDefaultItem() == self._pemObject:
				# Only change the default item to None if it wasn't self: if another 
				# object is the default item, setting self.DefaultButton = False 
				# shouldn't also set that other object's DefaultButton to False.
				self.Parent.SetDefaultItem(None)


	# Property definitions:
	CancelButton = property(_getCancelButton, _setCancelButton, None,
		_("Specifies whether this command button gets clicked on -Escape-."))
						
	DefaultButton = property(_getDefaultButton, _setDefaultButton, None, 
		_("Specifies whether this command button gets clicked on -Enter-."))


if __name__ == "__main__":
	import test
	test.Test().runTest(dButton)
