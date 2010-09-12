# -*- coding: utf-8 -*-
""" dFormMain.py """
import Tkinter
import dFormMixin as fm

class dFormMain(Tkinter.Tk, fm.dFormMixin):
	""" This is the main top-level form for the application.
	"""
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dFormMain
		preClass = Tkinter.Tk
		fm.dFormMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

		self.Size = (640,480)
		self.Position = (0,0)

#		if wx.Platform != '__WXMAC__':
#			self.CreateStatusBar()

		# Go figure: in order to get rid of the automatic sizing on forms,
		# you gotta set the sizer to something other than None!
#		self.Sizer = dSizer.dSizer("vertical")
#		self.Sizer.layout()



	def afterInit(self):
		self.Caption = "Dabo"
		self.setStatusText("Welcome to Dabo!")

	def setStatusText(self, text): pass

if __name__ == "__main__":
	import test
	test.Test().runTest(dFormMain)
