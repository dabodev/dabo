""" dFormMain.py """
import wx
import dFormMixin as fm
import dPanel, dIcons, dSizer
import dabo

import time

# Different platforms expect different frame types. Notably,
# most users on Windows expect and prefer the MDI parent/child
# type frames.

## pkm 06/09/2004: disabled MDI even on Windows. There are some issues that I
## don't have time to track down right now... better if it works
## on Windows similarly to Linux instead of not at all... if you
## want to enable MDI on Windows, just take out the "False and"
## in the below if statement, and do the same in dForm.py.

if False and wx.Platform == '__WXMSW__':	  # Microsoft Windows
	wxFrameClass = wx.MDIParentFrame
	wxPreFrameClass = wx.PreMDIParentFrame
else:
	wxFrameClass = wx.Frame
	wxPreFrameClass = wx.PreFrame

class dFormMain(wxFrameClass, fm.dFormMixin):
	""" This is the main top-level form for the application.
	"""
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dFormMain
		preClass = wxPreFrameClass
		fm.dFormMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
	
		self.Size = (640,480)
		self.Position = (0,0)

		if wx.Platform != '__WXMAC__':
			self.CreateStatusBar()

		# Go figure: in order to get rid of the automatic sizing on forms,
		# you gotta set the sizer to something other than None!
		self.Sizer = dSizer.dSizer("vertical")
		self.Sizer.layout()
	
		
	def afterInit(self):
		#dFormMain.doDefault()
		super(dFormMain, self).afterInit()
		self.Caption = "Dabo"
		self.setStatusText("Welcome to Dabo!")
		
		# This is to accomodate the Dabo icon, which has a white background.
		# We should set the white as transparent and set a mask, though.
		self.BackColor = "White"
		
		# Set up the Dabo icon
		self.bitmap = dIcons.getIconBitmap("dabo_lettering_250x100")
		self.needRedraw = False
		self.szTimer = wx.StopWatch()
		self.bindEvent(dabo.dEvents.Paint, self.__onPaint)
		self.bindEvent(dabo.dEvents.Idle, self.__onIdle)
		self.bindEvent(dabo.dEvents.Resize, self.__onResize)

	def __onPaint(self, evt):
		dc = wx.PaintDC(self)
		self.draw(dc)

	def __onResize(self, evt):
		self.needRedraw = True
		self.szTimer.Start()
	
	def __onIdle(self, evt):
		if self.needRedraw:
			if self.szTimer.Time() < 100:
				return
			self.szTimer.Pause()
			dc = wx.ClientDC(self)
			self.draw(dc)
			self.needRedraw = False

	def draw(self, dc):
		wd,ht = dc.GetSize()
		dc.DrawBitmap(self.bitmap, 10, (ht - 110))

if __name__ == "__main__":
	import test
	test.Test().runTest(dFormMain)
