""" dFormMain.py """
import Tkinter
import dFormMixin as fm

class dFormMain(Tkinter.Frame, fm.dFormMixin):
	""" This is the main top-level form for the application.
	"""
	def __init__(self):

		self._baseClass = dFormMain

#		self._beforeInit(pre)                  # defined in dPemMixin
#		self._tkObject = Tkinter.Frame()
		Tkinter.Frame.__init__(self)
		fm.dFormMixin.__init__(self)
#		self._afterInit()                      # defined in dPemMixin
		
	def afterInit(self):
		self.Caption = "Dabo"
		self.setStatusText("Welcome to Dabo!")

	def setStatusText(self, text): pass

if __name__ == "__main__":
	import test
	test.Test().runTest(dFormMain)
