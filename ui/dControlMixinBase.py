""" dControlMixin.py: Provide behavior common to all dControls """

import dabo
import dabo.ui
from dabo.dLocalize import _
import dabo.dEvents as dEvents

class dControlMixinBase(dabo.ui.dPemMixin):
	""" Provide common functionality for all controls.
	"""
	def __init__(self, name=None):
		if not name:
			name = self.Name
		
		try:
			self.Name = name
		except AttributeError:
			# Some toolkits (Tkinter) don't let objects change their
			# names after instantiation.
			pass

		dControlMixinBase.doDefault()


	def initEvents(self):
		dControlMixinBase.doDefault()
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
		
