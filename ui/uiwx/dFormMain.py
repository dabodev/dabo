""" dFormMain.py """
import wx
import dFormMixin as fm

# Different platforms expect different frame types. Notably,
# most users on Windows expect and prefer the MDI parent/child
# type frames.

# pkm 06/09/2004: disabled MDI even on Windows. There are some issues that I
#                 don't have time to track down right now... better if it works
#                 on Windows similarly to Linux instead of not at all... if you
#                 want to enable MDI on Windows, just take out the "False and"
#                 in the below if statement, and do the same in dForm.py.

if False and wx.Platform == '__WXMSW__':      # Microsoft Windows
	wxFrameClass = wx.MDIParentFrame
	wxPreFrameClass = wx.PreMDIParentFrame
else:
	wxFrameClass = wx.Frame
	wxPreFrameClass = wx.PreFrame

class dFormMain(wxFrameClass, fm.dFormMixin):
	""" This is the main top-level form for the application.
	"""
	def __init__(self):

		self._baseClass = dFormMain

		pre = wxPreFrameClass()
		self._beforeInit(pre)                  # defined in dPemMixin
		pre.Create(None, -1, "dFormMain")

		self.PostCreate(pre)
		
		self.Name = "dFormMain"
		self.Size = (640,480)
		self.Position = (0,0)

		fm.dFormMixin.__init__(self)

		if wx.Platform != '__WXMAC__':
			self.CreateStatusBar()

		self._afterInit()                      # defined in dPemMixin

		
	def afterInit(self):
		self.Caption = "Dabo"
		self.setStatusText("Welcome to Dabo!")


if __name__ == "__main__":
	import test
	test.Test().runTest(dFormMain)
