""" dControlMixin.py: Provide behavior common to all dControls """

import dabo
import dabo.ui
from dabo.dLocalize import _
import dabo.dEvents as dEvents

class dControlMixinBase(dabo.ui.dPemMixin):
	""" Provide common functionality for all controls.
	"""
	def __init__(self, name=None, _explicitName=True):
		if name is None:
			name = self.Name
		
		try:
			self._setName(name, _userExplicit=_explicitName)
		except AttributeError:
			# Some toolkits (Tkinter) don't let objects change their
			# names after instantiation.
			pass

		#dControlMixinBase.doDefault()
		super(dControlMixinBase, self).__init__()


