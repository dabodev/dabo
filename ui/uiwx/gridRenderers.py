# -*- coding: utf-8 -*-
import wx
import wx.grid
import dIcons

checkedBitmap = dIcons.getIconBitmap("boolRendererChecked")
uncheckedBitmap = dIcons.getIconBitmap("boolRendererUnchecked")

class BoolRenderer(wx.grid.PyGridCellRenderer): 
	"""The default wx Bool renderer is really ugly, so this is a replacement."""

	def __init__(self, *args, **kwargs):
		super(BoolRenderer, self).__init__(*args, **kwargs)


	def Draw(self, grid, attr, dc, rect, row, col, isSelected): 
		"""Customisation Point: Draw the data from grid in the rectangle with attributes using the dc""" 
		self.clip(dc, rect) 

		# We use our custom attr, not the one wx passes:
		attr = grid._Table.GetAttr(row, col)
		try: 
			bitmap = self.getValueBitmap(grid, row, col) 
			return self.drawBitmap(bitmap, attr, dc, rect, isSelected) 
		finally: 
			self.unclip(dc) 


	def GetBestSize(self, grid, attr, dc, row, col): 
		"""Customisation Point: Determine the appropriate (best) size for the control, return as wxSize 

		Note: You _must_ return a wxSize object.  Returning a two-value-tuple 
		won't raise an error, but the value won't be respected by wxPython. 
		""" 
		return wx.Size(checkedBitmap.GetWidth(), checkedBitmap.GetHeight())


	def getValueBitmap( self, grid, row, col ): 
		value = grid._Table.GetValue(row, col)
		if value:
			return checkedBitmap
		return uncheckedBitmap


	def drawBitmap( self, bitmap, attr, dc, rect, isSelected):
		# draw background:
		bkgrd = wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW) 	
		dc.SetBrush( wx.Brush(bkgrd, wx.SOLID)) 

		try: 
			dc.SetPen(wx.TRANSPARENT_PEN) 
			dc.DrawRectangle(rect.x, rect.y, rect.width, rect.height) 
		finally: 
			dc.SetPen(wx.NullPen) 
			dc.SetBrush(wx.NullBrush) 

		a = attr.GetAlignment()
		hbuffer = 5
		wbuffer = 3

		if (a[0] & wx.ALIGN_RIGHT) == wx.ALIGN_RIGHT:
			l = rect.width - bitmap.GetWidth() - wbuffer
		elif (a[0] & wx.ALIGN_CENTER_HORIZONTAL) == wx.ALIGN_CENTER_HORIZONTAL:
			l = (rect.width/2) - (bitmap.GetWidth()/2)
		else:
			l = wbuffer

		if (a[1] & wx.ALIGN_BOTTOM) == wx.ALIGN_BOTTOM:
			t = rect.height - bitmap.GetHeight() - hbuffer
		elif (a[1] & wx.ALIGN_CENTER_VERTICAL) == wx.ALIGN_CENTER_VERTICAL:
			t = (rect.height/2) - (bitmap.GetHeight()/2)
		else:
			t = hbuffer

		dc.DrawBitmap(bitmap, rect.x+l, rect.y+t) 


	def clip( self, dc, rect ): 
		"""Setup the clipping rectangle""" 
		dc.SetClippingRegion( rect.x, rect.y, rect.width, rect.height ) 


	def unclip( self, dc ): 
		"""Destroy the clipping rectangle""" 
		dc.DestroyClippingRegion( ) 





class YesNoBoolRenderer(wx.grid.PyGridCellRenderer): 
	def Draw(self, grid, attr, dc, rect, row, col, isSelected): 
		"""Customisation Point: Draw the data from grid in the rectangle with attributes using the dc""" 
		self.clip(dc, rect) 

		# We use our custom attr, not the one wx passes:
		attr = grid._Table.GetAttr(row, col)
		try: 
			txt = self.getValueText(grid, row, col) 
			return self.drawText(txt, attr, dc, rect) 
		finally: 
			self.unclip(dc) 


	def getValueText( self, grid, row, col ): 
		value = grid._Table.GetValue(row, col)
		if value:
			return "YES"
		return "NO"


	def drawText( self, txt, attr, dc, rect):
		if txt == "NO":
			dc.SetTextForeground((128, 0, 0))
		else:
			dc.SetTextForeground((0, 128, 0))
		dc.DrawText(txt, rect.x, rect.y) 


	def clip( self, dc, rect ): 
		"""Setup the clipping rectangle""" 
		dc.SetClippingRegion( rect.x, rect.y, rect.width, rect.height ) 


	def unclip( self, dc ): 
		"""Destroy the clipping rectangle""" 
		dc.DestroyClippingRegion( ) 

