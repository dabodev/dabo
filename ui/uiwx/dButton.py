import warnings, wx, dabo, dabo.ui

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
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)


	def _initEvents(self):
		super(dButton, self)._initEvents()
		self.Bind(wx.EVT_BUTTON, self._onWxHit)
		
		
	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getCancelButton(self):
		# need to implement
		return False

	def _setCancelButton(self, value):
		warnings.warn("CancelButton isn't implemented yet.", Warning)	
	
	def _getDefaultButton(self):
		return self._pemObject.GetParent().GetDefaultItem() == self._pemObject
	def _setDefaultButton(self, value):
		if value:
			self._pemObject.GetParent().SetDefaultItem(self._pemObject)
			if wx.Platform == '__WXGTK__':
				warnings.warn("DefaultButton doesn't seem to work on GTK.", Warning)
		else:
			if self._pemObject.GetParent().GetDefaultItem() == self._pemObject:
				# Only change the default item to None if it wasn't self: if another object
				# is the default item, setting self.DefaultButton = False shouldn't also set
				# that other object's DefaultButton to False.
				self.SetDefaultItem(None)


	# Property definitions:
	CancelButton = property(_getCancelButton, _setCancelButton, None,
		_("Specifies whether this command button gets clicked on -Escape-."))
						
	DefaultButton = property(_getDefaultButton, _setDefaultButton, None, 
		_("Specifies whether this command button gets clicked on -Enter-."))


if __name__ == "__main__":
	import test
	test.Test().runTest(dButton)
