import warnings, wx, dabo
import dControlMixin as cm
from dabo.dLocalize import _
from dIcons import getIconBitmap
import dEvents

class dBitmapButton(wx.BitmapButton, cm.dControlMixin):
	""" Allows the user to cause an action to occur by pushing a button.
	"""
	def __init__(self, parent, id=-1, bitmap=None, name="dBitmapButton", 
				style=0, *args, **kwargs):
		
		self._baseClass = dBitmapButton

		pre = wx.PreBitmapButton()
		self._beforeInit(pre)                  # defined in dPemMixin
		
		if bitmap is None:
			# Default to the Dabo icon
			bitmap = getIconBitmap("daboIcon016")
		
		pre.Create(parent, id, bitmap, name=name, style=style|pre.GetWindowStyle(), *args, **kwargs)

		self.PostCreate(pre)
		
		cm.dControlMixin.__init__(self, name)
		self._afterInit()                      # defined in dPemMixin


	def initEvents(self):
		# init the common events:
		cm.dControlMixin.initEvents(self)

		# Respond to EVT_BUTTON and raise dEvents.Button:
		self.bindEvent(wx.EVT_BUTTON, self._onWxButton)
		
		# init the widget's specialized event(s):
		self.bindEvent(dEvents.Button, self.onButton)

	# Event callback methods (override in subclasses):
	def onButton(self, event):
		if self.debug:
			dabo.infoLog.write(_("onButton received by %s") % self.Name)
		event.Skip()

	def _onWxButton(self, event):
		self.raiseEvent(dEvents.Button)
		event.Skip()
		
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
			self._pemObject.SetDefaultItem(None)


	# Property definitions:
	CancelButton = property(_getCancelButton, _setCancelButton, None,
						_('Specifies whether this Bitmap button gets clicked on -Escape-. (bool)'))
						
	DefaultButton = property(_getDefaultButton, _setDefaultButton, None, 
						_('Specifies whether this Bitmap button gets clicked on -Enter-. (bool)'))


if __name__ == "__main__":
	import test
	test.Test().runTest(dBitmapButton)
