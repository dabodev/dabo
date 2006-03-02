import wx
import dabo
from dabo.dLocalize import _

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
from dabo.ui import makeDynamicProperty


class dPanel(wx.Panel, cm.dControlMixin):
	"""Creates a panel, a basic container for controls.

	Panels can contain subpanels to unlimited depth, making them quite
	flexible for many uses. Consider laying out your forms on panels
	instead, and then adding the panel to the form.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dPanel
		self._buffered = None
		preClass = wx.PrePanel
		style = self._extractKey((properties, kwargs), "style", 0)
		style = style | wx.TAB_TRAVERSAL
		kwargs["style"] = style
		buff = self._extractKey((properties, kwargs), "Buffered", False)
		kwargs["Buffered"] = buff
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)


	def layout(self):
		""" Wrap the wx version of the call, if possible. """
		self.Layout()
		try:
			# Call the Dabo version, if present
			self.Sizer.layout()
		except:
			pass
	
	
	def _onPaintBuffer(self, evt):
		dc = wx.BufferedPaintDC(self, self._buffer)
	
	
	def _onResizeBuffer(self, evt):
		evt.Skip()
		self._buffer = wx.EmptyBitmap(max(1, self.Width), max(1, self.Height))
		self.__updateDrawing()
	
	
	def __updateDrawing(self):
		dc = wx.BufferedDC(wx.ClientDC(self), self._buffer)
		dc.Clear() # make sure you clear the bitmap! 
		self._redraw(dc)
		

	def _redraw(self, dc=None):
		if self._buffered:
			# Override the base call to provide a buffered DC.
			try:
				self._buffer
			except:
				# This is being called way too early; skip this call
				return
			if dc is None:
				dc = wx.BufferedDC(wx.ClientDC(self), self._buffer)
				dc.Clear() # make sure you clear the bitmap! 
		super(dPanel, self)._redraw(dc)


	def _getBuffered(self):
		return self._buffered

	def _setBuffered(self, val):
		if self._buffered == val:
			return
		self._buffered = val
		if val:
			# Set up the double-buffering.
			self._buffer = wx.EmptyBitmap(max(1, self.Width), max(1, self.Height))
			self.Bind(wx.EVT_PAINT, self._onPaintBuffer)
			self.Bind(wx.EVT_SIZE, self._onResizeBuffer)
		else:
			self.Unbind(wx.EVT_PAINT)
			self.Unbind(wx.EVT_SIZE)
		

	Buffered = property(_getBuffered, _setBuffered, None,
			_("Does this panel use double-buffering to create smooth redrawing?  (bool)"))
	
		

class dScrollPanel(wx.ScrolledWindow, cm.dControlMixin):
	""" This is a basic container for controls that allows scrolling.

	Panels can contain subpanels to unlimited depth, making them quite
	flexible for many uses. Consider laying out your forms on panels
	instead, and then adding the panel to the form.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._horizontalScroll = self._verticalScroll = True
		self._baseClass = dScrollPanel
		preClass = wx.PreScrolledWindow
		if "style" not in kwargs:
			kwargs["style"] = wx.TAB_TRAVERSAL
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
#		self.SetScrollbars(10, 10, -1, -1)
	

	def layout(self):
		""" Wrap the wx version of the call, if possible. """
		self.Layout()
		for child in self.Children:
			try:
				child.layout()
			except: pass
		try:
			# Call the Dabo version, if present
			self.Sizer.layout()
		except:
			pass
			

	def _getHorizontalScroll(self):
		return self._horizontalScroll

	def _setHorizontalScroll(self, val):
		self._horizontalScroll = val
		self.EnableScrolling(self._horizontalScroll, self._verticalScroll)
		

	def _getVerticalScroll(self):
		return self._verticalScroll

	def _setVerticalScroll(self, val):
		self._verticalScroll = val
		self.EnableScrolling(self._horizontalScroll, self._verticalScroll)
		

	HorizontalScroll = property(_getHorizontalScroll, _setHorizontalScroll, None,
			_("Controls whether this object will scroll horizontally (default=True)  (bool)"))
	DynamicHorizontalScroll = makeDynamicProperty(HorizontalScroll)
	
	VerticalScroll = property(_getVerticalScroll, _setVerticalScroll, None,
			_("Controls whether this object will scroll vertically (default=True)  (bool)"))
	DynamicVerticalScroll = makeDynamicProperty(VerticalScroll)
	

class _dPanel_test(dPanel):
	def initProperties(self):
		self.BackColor = "wheat"
		self.Hover = True

	def afterInit(self):
		self.addObject(dPanel, BackColor = "green")

	def onHover(self):
		self._normBack = self.BackColor
		self.BackColor = "yellow"
	
	def endHover(self):
		self.BackColor = self._normBack

	def onMouseLeftDown(self, evt):
		print "mousedown"

	def onPaint(self, evt):
		print "paint"

	def onKeyDown(self, evt):
		print evt.EventData["keyCode"]


class _dScrollPanel_test(dScrollPanel):
	def initProperties(self):
		self.BackColor = "wheat"

	def afterInit(self):
		subpan = self.addObject(dPanel, BackColor = "green")
		subpan.bindEvent(dabo.dEvents.KeyDown, self.onKeyDown)
		self.SetScrollbars(10,10,100,100)

	def onMouseLeftDown(self, evt):
		print "mousedown"
		self.SetFocusIgnoringChildren()

	def onPaint(self, evt):
		print "paint"

	def onKeyDown(self, evt):
		print evt.EventData["keyCode"]



if __name__ == "__main__":
	import test
	test.Test().runTest(_dPanel_test)
	test.Test().runTest(_dScrollPanel_test)




