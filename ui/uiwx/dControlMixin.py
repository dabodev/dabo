import wx
import dabo.ui
from dabo.ui.dControlMixinBase import dControlMixinBase
import dabo.dEvents as dEvents

class dControlMixin(dControlMixinBase):
	
	def _onWxHit(self, evt):
		self.raiseEvent(dEvents.Hit, evt)
		
	def getCaptureBitmap(self):
		"""Returns a bitmap snapshot of self, as it appears in the UI at this moment.
		"""
		
		## Not sure if this belongs here or not, but didn't want to lose it.
		
		rect = self.GetRect()
		bmp = wx.EmptyBitmap(rect.width, rect.height)
		memdc = wx.MemoryDC()
		memdc.SelectObject(bmp)
		dc = wx.WindowDC(self)
		memdc.Blit(0,0, rect.width, rect.height, dc, rect.x, rect.y)
		memdc.SelectObject(wx.NullBitmap)
		return bmp
