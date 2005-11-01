""" dFormMain.py """
import wx
import dFormMixin as fm
import dPanel, dIcons, dSizer
import dabo

import time


class dFormMainBase(fm.dFormMixin):
	""" This is the main top-level form for the application.
	"""
	def __init__(self, preClass, parent=None, properties=None, *args, **kwargs):
		fm.dFormMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
	
		self.Size = (640,480)
		self.Position = (0,0)

		if wx.Platform != '__WXMAC__':
			self.CreateStatusBar()

		
	def _afterInit(self):
		super(dFormMainBase, self)._afterInit()
		
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

	
	def _beforeClose(self, evt=None):
		forms2close = [frm for frm in self.Application.uiForms
				if frm is not self]
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


class dFormMainSDI(wx.Frame, dFormMainBase):
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dFormMain
		preClass = wx.PreFrame
		dFormMainBase.__init__(self, preClass, parent, properties, *args, **kwargs)


class dFormMainParentMDI(wx.MDIParentFrame, dFormMainBase):
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dFormMain
		preClass = wx.PreMDIParentFrame
		dFormMainBase.__init__(self, preClass, parent, properties, *args, **kwargs)


if dabo.settings.MDI:
	dFormMain = dFormMainParentMDI
else:
	dFormMain = dFormMainSDI


if __name__ == "__main__":
	import test
	test.Test().runTest(dFormMain)
