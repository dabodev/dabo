# -*- coding: utf-8 -*-
import Tkinter, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("tk")

import dControlMixin as dControlMixin

class dPanel(Tkinter.Frame, dControlMixin.dControlMixin):
	""" This is a basic container for controls.

	Panels can contain subpanels to unlimited depth, making them quite
	flexible for many uses. Consider laying out your forms on panels
	instead, and then adding the panel to the form.
	"""

	def __init__(self, master, cnf = {}, name="dPanel", *args, **kwargs):

		self._baseClass = dPanel

		self._beforeInit()
		Tkinter.Frame.__init__(self, master, cnf, name=name, *args, **kwargs)

		dControlMixin.dControlMixin.__init__(self, name)

		self._afterInit()

		self.pack()
