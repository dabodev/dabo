""" dControlMixin.py: Provide behavior common to all dControls """

import dabo
import dPemMixin as pm
from dabo.dLocalize import _
import dabo.dEvents as dEvents

class dControlMixin(pm.dPemMixin):
	""" Provide common functionality for all controls.
	"""
	def __init__(self, name=None):
		if not name:
			name = self.Name
		self.Name = name		

		dControlMixin.doDefault()


	def initEvents(self):
		dControlMixin.doDefault()
		# convenience-bind the widget's specialized event(s):
		self.bindEvent(dEvents.Hit, self.onHit)

	def _onWxHit(self, event):
		self.raiseEvent(dEvents.Hit, event)
		event.Skip()
		
	def onHit(self, event):
		""" Occurs when the control's default action has taken place, such as
		a click on a CommandButton, a character entered in a TextBox, an item
		being picked in a ListBox, a timer reaching its interval, etc.
		"""
		if self.debug:
			dabo.infoLog.write(_("%s: onHit() called.") % self.Name)
		
