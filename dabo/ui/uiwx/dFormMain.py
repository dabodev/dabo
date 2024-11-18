# -*- coding: utf-8 -*-
import time
import wx
import dabo

if __name__ == "__main__":
	import dabo.ui
	dabo.ui.loadUI("wx")
	if __package__ is None:
		import dabo.ui.uiwx
		__package__ = "dabo.ui.uiwx"

import dFormMixin as fm


class dFormMainBase(fm.dFormMixin):
	"""This is the main top-level form for the application."""
	def __init__(self, preClass, parent=None, properties=None, *args, **kwargs):
		fm.dFormMixin.__init__(self, preClass, parent, properties, *args, **kwargs)


	def _beforeClose(self, evt=None):
		forms2close = [frm for frm in self.Application.uiForms
				if frm is not self and not isinstance(frm, dabo.ui.deadObject)]
		while forms2close:
			frm = forms2close[0]
			# This will allow forms to veto closing (i.e., user doesn't
			# want to save pending changes).
			if frm.close() == False:
				# The form stopped the closing process. The user
				# must deal with this form (save changes, etc.)
				# before the app can exit.
				frm.bringToFront()
				return False
			else:
				forms2close.remove(frm)




class dFormMain(dFormMainBase, wx.Frame):
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dFormMain

		if dabo.MDI:
			# Hack this into an MDI Parent:
			dFormMain.__bases__ = (dFormMainBase, wx.MDIParentFrame)
			if dabo.ui.phoenix:
				preClass = wx.MDIParentFrame
			else:
				preClass = wx.PreMDIParentFrame
			self._mdi = True
		else:
			# This is a normal SDI form:
			dFormMain.__bases__ = (dFormMainBase, wx.Frame)
			if dabo.ui.phoenix:
				preClass = wx.Frame
			else:
				preClass = wx.PreFrame
			self._mdi = False
		## (Note that it is necessary to run the above block each time, because
		##  we are modifying the dFormMain class definition globally.)

		dFormMainBase.__init__(self, preClass, parent, properties, *args, **kwargs)



if __name__ == "__main__":
	from . import test
	test.Test().runTest(dFormMain)
