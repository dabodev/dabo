import wx
import dabo
import dPemMixin

class dSizerMixin(dabo.common.dObject):
	def append(self, item, layout="normal", proportion=0, alignment=("top", "left"), 
		border=0, borderFlags=("all",)):
		"""Append an object or a spacer to the sizer.
		
		layout: 
			"expand": The object will expand to fill in the extra space
			"fixed": The object will not be resized
			"normal": The sizer will determine how to lay out the object. (default)
			
		proportion: The relative space this object should get in relation to the 
			other objects. Default has all objects getting 0, equal share.
			
		alignment: The horizontal and vertical alignment of the object in the sizer.
			This is a tuple: set it like ("left", "top") or ("center", "middle").
			
		border: The width of the border. Default is 0, no border.
		
		borderFlags: A tuple containing the locations to draw the border, such as
			("all") or ("top", "left", "bottom"). Default is ("all").
			
		For the most common usage of adding an object to the sizer, just do:
			
			sizer.append(object)
			
			or
			
			sizer.append(object, "expand")
			
		"""
		if type(layout) == type(0):
			# proportion was passed first
			layout, proportion = proportion, layout
			# in case layout wasn't specified
			if type(layout) == type(0):
				layout = "normal"
		
		if type(item) == type(tuple()):
			# spacer
			self.Add(item)
		else:
			# item is the window to add to the sizer
			_wxFlags = self._getWxFlags(alignment, borderFlags, layout)
			self.Add(item, proportion, _wxFlags, border)
			

	def insert(self, index, item, layout="normal", proportion=0, alignment=("top", "left"), 
		border=0, borderFlags=("all",)):
		"""Insert an object or a spacer to the sizer.
		
		index: The index of the existing sizer item that you want to insert in 
			front of.
			
		layout: 
			"expand": The object will expand to fill in the extra space
			"fixed": The object will not be resized
			"normal": The sizer will determine how to lay out the object. (default)
			
		proportion: The relative space this object should get in relation to the 
			other objects. Default has all objects getting 0, equal share.
			
		alignment: The horizontal and vertical alignment of the object in the sizer.
			This is a tuple: set it like ("left", "top") or ("center", "middle").
			
		border: The width of the border. Default is 0, no border.
		
		borderFlags: A tuple containing the locations to draw the border, such as
			("all") or ("top", "left", "bottom"). Default is ("all").
			
		For the most common usage of inserting an object to the sizer, just do:
			
			sizer.insert(index, object)
			
			or
			
			sizer.insert(index, object, "expand")
			
		"""
		if type(layout) == type(0):
			# proportion was passed first
			layout, proportion = proportion, layout
			# in case layout wasn't specified
			if type(layout) == type(0):
				layout = "normal"
		
		if type(item) == type(tuple()):
			# spacer
			self.Insert(index, item)
		else:
			# item is the window to add to the sizer
			_wxFlags = self._getWxFlags(alignment, borderFlags, layout)
			self.Insert(index, item, proportion, _wxFlags, border)

	
	def layout(self):
		"""Layout the items in the sizer.
		
		This is handled automatically when the sizer is resized, but you'll have
		to call it manually after you are done adding items to the sizer.
		"""
		self.Layout()
	
	
	def prepend(self, *args, **kwargs):
		"""Insert the item at the beginning of the sizer layout.
		
		See append() for the parameters to use.
		"""
		self.insert(0, *args, **kwargs)			
	
	
	def drawOutline(self, win):
		""" There are some cases where being able to see the sizer
		is helpful, such as at design time. This method can be called
		to see the outline; it needs to be called whenever the containing
		window is resized or repainted.
		"""
		if self.Orientation == "Vertical":
			self.outlineColor = wx.BLUE
		else:
			self.outlineColor = wx.RED
		x, y = self.GetPosition()
		w, h = self.GetSize()
		# Offset
		off = 0
		
		dc = wx.ClientDC(win)
		dc.SetPen(wx.Pen(self.outlineColor, 1, wx.SHORT_DASH))
		dc.SetBrush(wx.TRANSPARENT_BRUSH)
		dc.SetLogicalFunction(wx.COPY)
		# Draw the outline
		dc.DrawRectangle( x+off, y+off, w-(2*off), h-(2*off) )

		
	def _getWxFlags(self, alignment, borderFlags, layout):
		# If alignment is passed as a single string instead of a tuple, 
		# convert it.
		if type(alignment) == type(""):
			alignment = (alignment, )
		if type(borderFlags) == type(""):
			borderFlags = (borderFlags, )
		_wxFlags = 0
		for flag in [flag.lower() for flag in alignment]:
			if flag == "left":
				_wxFlags = _wxFlags | wx.ALIGN_LEFT
			elif flag == "right":
				_wxFlags = _wxFlags | wx.ALIGN_RIGHT
			elif flag in ("center", "centre"):
				_wxFlags = _wxFlags | wx.ALIGN_CENTER
			elif flag == "top":
				_wxFlags = _wxFlags | wx.ALIGN_TOP
			elif flag == "bottom":
				_wxFlags = _wxFlags | wx.ALIGN_BOTTOM
			elif flag == "middle":
				_wxFlags = _wxFlags | wx.ALIGN_CENTER_VERTICAL

		for flag in [flag.lower() for flag in borderFlags]:
			if flag == "left":
				_wxFlags = _wxFlags | wx.LEFT
			elif flag == "right":
				_wxFlags = _wxFlags | wx.RIGHT
			elif flag == "top":
				_wxFlags = _wxFlags | wx.TOP
			elif flag == "bottom":
				_wxFlags = _wxFlags | wx.BOTTOM
			elif flag == "all":
				_wxFlags = _wxFlags | wx.ALL

		if layout.lower() == "expand":
			_wxFlags = _wxFlags | wx.EXPAND
		elif layout.lower() == "fixed":
			_wxFlags = _wxFlags | wx.FIXED_MINSIZE

		return _wxFlags				

				
 	def _getOrientation(self):
		o = self.GetOrientation()
		
		if o == wx.VERTICAL:
			return "Vertical"
		elif o == wx.HORIZONTAL:
			return "Horizontal"
		else:
			return "?"
			
	def _setOrientation(self, val):
		if val[0].lower() == "v":
			self.SetOrientation(wx.VERTICAL)
		else:
			self.SetOrientation(wx.HORIZONTAL)
			
	Orientation = property(_getOrientation, _setOrientation, None, 
		"Sets the orientation of the sizer, either 'Vertical' or 'Horizontal'.")

