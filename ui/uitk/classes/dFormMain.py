""" dFormMain.py """
import Tkinter
import dFormMixin as fm

class dFormMain(Tkinter.Tk, fm.dFormMixin):
	""" This is the main top-level form for the application.
	"""
	def __init__(self):

		self._baseClass = dFormMain

		self._beforeInit()
		Tkinter.Tk.__init__(self)
		fm.dFormMixin.__init__(self)
		self._afterInit()
		
	def afterInit(self):
		self.Caption = "Dabo"
		self.setStatusText("Welcome to Dabo!")

	def setStatusText(self, text): pass

if __name__ == "__main__":
	import test
	test.Test().runTest(dFormMain)
