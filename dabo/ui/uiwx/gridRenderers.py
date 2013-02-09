# -*- coding: utf-8 -*-
import dabo
import wx
import wx.grid
import dIcons



class ImageRenderer(wx.grid.PyGridCellRenderer):
	"""Used to display small images in a column."""

	def __init__(self, *args, **kwargs):
		self._lastBitmap = None
		super(ImageRenderer, self).__init__(*args, **kwargs)


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
		"""
		Customisation Point: Determine the appropriate (best) size for the control, return as wxSize

		.. note::

			You _must_ return a wxSize object.  Returning a two-value-tuple
			won't raise an error, but the value won't be respected by wxPython.
		"""
		try:
			return wx.Size(self._lastBitmap.GetWidth(), self._lastBitmap.GetHeight())
		except AttributeError:
			# Guess
			return wx.Size(16, 16)


	def getValueBitmap(self, grid, row, col):
		"""
		Take the local _imageDict and update it with the grid's dict, if any. Use
		that to look up the image to use for the given value. If not found, then
		see if that image is a 'standard' dabo image. If none of these return a value,
		return None, which won't draw anything.
		"""
		val = grid._Table.GetValue(row, col, convertNoneToString=False)
		try:
			imgLookup = grid.imageDict[val]
		except (AttributeError, KeyError):
			# Either no 'imageDict' attribute for the grid, or there is such an
			# att and the key is not found. Try standard images.
			ret = dabo.ui.strToBmp(val)
		return ret


	def drawBitmap(self, bitmap, attr, dc, rect, isSelected):
		if not bitmap:
			return
		# draw background:
		if isSelected:
			syscolor = wx.SYS_COLOUR_HIGHLIGHT
		else:
			syscolor = wx.SYS_COLOUR_WINDOW

		bkgrd = wx.SystemSettings_GetColour(syscolor)
		dc.SetBrush(wx.Brush(bkgrd, wx.SOLID))

		try:
			dc.SetPen(wx.TRANSPARENT_PEN)
			dc.DrawRectangle(rect.x, rect.y, rect.width, rect.height)
		finally:
			dc.SetPen(wx.NullPen)
			dc.SetBrush(wx.NullBrush)

		a = attr.GetAlignment()
		hbuffer = 0
		wbuffer = 0

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


	def clip(self, dc, rect):
		"""Setup the clipping rectangle"""
		dc.SetClippingRegion(rect.x, rect.y, rect.width, rect.height)


	def unclip(self, dc):
		"""Destroy the clipping rectangle"""
		dc.DestroyClippingRegion()



class BoolRenderer(wx.grid.PyGridCellRenderer):
	"""The default wx Bool renderer is really ugly, so this is a replacement."""

	def __init__(self, *args, **kwargs):
		super(BoolRenderer, self).__init__(*args, **kwargs)
		self.checkedBitmap = dIcons.getIconBitmap("boolRendererChecked")
		self.uncheckedBitmap = dIcons.getIconBitmap("boolRendererUnchecked")



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
		"""
		Customisation Point: Determine the appropriate (best) size for the control, return as wxSize

		.. note::
			You _must_ return a wxSize object.  Returning a two-value-tuple
			won't raise an error, but the value won't be respected by wxPython.

		"""
		return wx.Size(self.checkedBitmap.GetWidth(), self.checkedBitmap.GetHeight())


	def getValueBitmap(self, grid, row, col):
		value = grid._Table.GetValue(row, col, convertNoneToString=False)
		if value:
			return self.checkedBitmap
		return self.uncheckedBitmap


	def drawBitmap(self, bitmap, attr, dc, rect, isSelected):
		# draw background:
		if isSelected:
			syscolor = wx.SYS_COLOUR_HIGHLIGHT
		else:
			syscolor = wx.SYS_COLOUR_WINDOW

		bkgrd = wx.SystemSettings_GetColour(syscolor)
		dc.SetBrush(wx.Brush(bkgrd, wx.SOLID))

		try:
			dc.SetPen(wx.TRANSPARENT_PEN)
			dc.DrawRectangle(rect.x, rect.y, rect.width, rect.height)
		finally:
			dc.SetPen(wx.NullPen)
			dc.SetBrush(wx.NullBrush)

		a = attr.GetAlignment()
		hbuffer = 0
		wbuffer = 0

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


	def clip(self, dc, rect):
		"""Setup the clipping rectangle"""
		dc.SetClippingRegion(rect.x, rect.y, rect.width, rect.height)


	def unclip(self, dc):
		"""Destroy the clipping rectangle"""
		dc.DestroyClippingRegion()



class AbstractTextRenderer(wx.grid.PyGridCellRenderer):
	"""
	This is a starting point for all renderers that simply involve controlling
	the text displayed in a cell.
	"""
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


	def getValueText(self, grid, row, col):
		"""
		Return the text you want displayed in the cell. By default
		the value in the cell is returned unchanged; override for
		your class's needs.
		"""
		value = grid.getValue(row, col)
		return value


	def drawText(self, txt, attr, dc, rect):
		"""Customize this method to set different background colors, etc."""
		dc.DrawText(txt, rect.x, rect.y)


	def clip(self, dc, rect):
		"""Setup the clipping rectangle"""
		dc.SetClippingRegion(rect.x, rect.y, rect.width, rect.height)


	def unclip(self, dc):
		"""Destroy the clipping rectangle"""
		dc.DestroyClippingRegion()



class YesNoBoolRenderer(AbstractTextRenderer):
	def getValueText(self, grid, row, col):
		value = grid._Table.GetValue(row, col)
		if value:
			return "YES"
		return "NO"


	def drawText(self, txt, attr, dc, rect):
		if txt == "NO":
			dc.SetTextForeground((128, 0, 0))
		else:
			dc.SetTextForeground((0, 128, 0))
		dc.DrawText(txt, rect.x, rect.y)
