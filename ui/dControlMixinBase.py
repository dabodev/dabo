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

		#dControlMixinBase.doDefault()
		super(dControlMixinBase, self).__init__()


