import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
from dabo.dLocalize import _
import dabo.dEvents as dEvents

class dCommandButton(wx.Button, cm.dControlMixin):
	""" Allows the user to cause an action to occur by pushing a button.
	"""

	def __init__(self, parent, id=-1, name="dCommandButton", style=0,
				 *args, **kwargs):

		self._baseClass = dCommandButton

		pre = wx.PreButton()
		self._beforeInit(pre)
		pre.Create(parent, id, name=name, style=style|pre.GetWindowStyle(),
				   *args, **kwargs)

		self.PostCreate(pre)
		
		cm.dControlMixin.__init__(self, name)
		self._afterInit()


	def initEvents(self):
		#dCommandButton.doDefault()
		super(dCommandButton, self).initEvents()

		# Respond to EVT_BUTTON and raise dEvents.Hit:
		self.Bind(wx.EVT_BUTTON, self._onWxHit)
		
		
	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getCancelButton(self):
		# need to implement
		return False

	def _setCancelButton(self, value):
		warnings.warn(Warning, "CancelButton isn't implemented yet.")	
	
	def _getDefaultButton(self):
		return self._pemObject.Parent.GetDefaultItem() == self
	def _setDefaultButton(self, value):
		if value:
			self._pemObject.Parent.SetDefaultItem(self)
			if wx.Platform == '__WXGTK__':
				warnings.warn(Warning, "DefaultButton doesn't seem to work on GTK.")
		else:
			self._pemObject.Parent.SetDefaultItem(None)


	# Property definitions:
	CancelButton = property(_getCancelButton, _setCancelButton, None,
						_('Specifies whether this command button gets clicked on -Escape-. (bool)'))
						
	DefaultButton = property(_getDefaultButton, _setDefaultButton, None, 
						_('Specifies whether this command button gets clicked on -Enter-. (bool)'))


if __name__ == "__main__":
	import test
	test.Test().runTest(dCommandButton)
