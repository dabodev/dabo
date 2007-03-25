import wx
import dabo
from dabo.dLocalize import _

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
from dabo.ui import makeDynamicProperty


class _PanelMixin(cm.dControlMixin):
	def __init__(self, preClass, parent, properties=None, attProperties=None, 
			*args, **kwargs):
		self._minSizerWidth = 10
		self._minSizerHeight = 10
		self._alwaysResetSizer = False
		self._buffered = None
		buff = self._extractKey(attProperties, "Buffered", None)
		if buff is not None:
			buff = (buff == "True")
		else:
			buff = self._extractKey((properties, kwargs), "Buffered", False)
		kwargs["Buffered"] = buff
		style = self._extractKey((properties, kwargs), "style", 0)
		style = style | wx.TAB_TRAVERSAL
		kwargs["style"] = style
		# For performance, store this at init
		self._platformIsWindows = (self.Application.Platform == "Win")
		cm.dControlMixin.__init__(self, preClass, parent, properties, attProperties, 
				*args, **kwargs)
	

	def layout(self, resetMin=False):
		""" Wrap the wx version of the call, if possible. """
		if resetMin or self._alwaysResetSizer:
			# Set the panel's minimum size back to zero. This is sometimes
			# necessary when the items in the panel have reduced in size.
			self.SetMinSize((self.MinSizerWidth, self.MinSizerHeight))
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
		if self._platformIsWindows:
			self.refresh()


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
		super(_PanelMixin, self)._redraw(dc)


	def _getAlwaysResetSizer(self):
		return self._alwaysResetSizer

	def _setAlwaysResetSizer(self, val):
		if self._constructed():
			self._alwaysResetSizer = val
		else:
			self._properties["AlwaysResetSizer"] = val


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
		

	def _getMinSizerHeight(self):
		return self._minSizerHeight

	def _setMinSizerHeight(self, val):
		if self._constructed():
			self._minSizerHeight = val
		else:
			self._properties["MinSizerHeight"] = val


	def _getMinSizerWidth(self):
		return self._minSizerWidth

	def _setMinSizerWidth(self, val):
		if self._constructed():
			self._minSizerWidth = val
		else:
			self._properties["MinSizerWidth"] = val


	AlwaysResetSizer = property(_getAlwaysResetSizer, _setAlwaysResetSizer, None,
			_("""When True, the sizer settings are always cleared before a layout() is called.
			This may be necessary when a panel needs to reduce its size. Default=False   (bool)"""))
	
	Buffered = property(_getBuffered, _setBuffered, None,
			_("Does this panel use double-buffering to create smooth redrawing?  (bool)"))

	MinSizerHeight = property(_getMinSizerHeight, _setMinSizerHeight, None,
			_("Minimum height for the panel. Default=10px  (int)"))
	
	MinSizerWidth = property(_getMinSizerWidth, _setMinSizerWidth, None,
			_("Minimum width for the panel. Default=10px  (int)"))
	
	


class dPanel(_PanelMixin, wx.Panel):
	"""Creates a panel, a basic container for controls.

	Panels can contain subpanels to unlimited depth, making them quite
	flexible for many uses. Consider laying out your forms on panels
	instead, and then adding the panel to the form.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dPanel
		preClass = wx.PrePanel
		_PanelMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)
	
		

class dScrollPanel(_PanelMixin, wx.ScrolledWindow):
	""" This is a basic container for controls that allows scrolling.

	Panels can contain subpanels to unlimited depth, making them quite
	flexible for many uses. Consider laying out your forms on panels
	instead, and then adding the panel to the form.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._horizontalScroll = self._verticalScroll = True
		self._baseClass = dScrollPanel
		preClass = wx.PreScrolledWindow
		_PanelMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)
		self.SetScrollRate(10, 10)
#		self.SetScrollbars(10, 10, -1, -1)
			

	def _getChildren(self):
		ret = super(dScrollPanel, self)._getChildren()
		return [kid for kid in ret
				if isinstance(kid, dabo.ui.dPemMixinBase.dPemMixinBase)]

	def _setChildren(self, val):
		super(dScrollPanel, self)._setChildren(val)


	def _getHorizontalScroll(self):
		return self._horizontalScroll

	def _setHorizontalScroll(self, val):
		self._horizontalScroll = val
		self.EnableScrolling(self._horizontalScroll, self._verticalScroll)
		rt = self.GetScrollPixelsPerUnit()
		self.SetScrollRate({True:rt[0], False:0}[val], rt[1])
		

	def _getVerticalScroll(self):
		return self._verticalScroll

	def _setVerticalScroll(self, val):
		self._verticalScroll = val
		self.EnableScrolling(self._horizontalScroll, self._verticalScroll)
		rt = self.GetScrollPixelsPerUnit()
		self.SetScrollRate(rt[0], {True:rt[1], False:0}[val])
		

	Children = property(_getChildren, _setChildren, None,
			_("""Child controls of this panel. This excludes the wx-specific 
			scroll bars  (list of objects)"""))
	
	HorizontalScroll = property(_getHorizontalScroll, _setHorizontalScroll, None,
			_("Controls whether this object will scroll horizontally (default=True)  (bool)"))
	
	VerticalScroll = property(_getVerticalScroll, _setVerticalScroll, None,
			_("Controls whether this object will scroll vertically (default=True)  (bool)"))


	DynamicHorizontalScroll = makeDynamicProperty(HorizontalScroll)
	DynamicVerticalScroll = makeDynamicProperty(VerticalScroll)
	

class _dPanel_test(dPanel):
	def initProperties(self):
		self.BackColor = "wheat"
		self.Hover = True

	def afterInit(self):
		self.addObject(dPanel, BackColor = "green")

	def onHover(self, evt):
		self._normBack = self.BackColor
		self.BackColor = dabo.dColors.randomColor()
	
	def endHover(self, evt):
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




