import wx
import dabo
import dPemMixin

class dSizerMixin(dabo.common.dObject):
	def append(self, item, layout="normal", proportion=0, alignment=("top", "left"), 
		border=None, borderFlags=None):
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
		if type(layout) == int:
			# proportion was passed first
			layout, proportion = proportion, layout
			# in case layout wasn't specified
			if type(layout) == int:
				layout = "normal"
		
		if type(item) == tuple:
			# spacer
			self.Add(item, proportion)
		else:
			# item is the window to add to the sizer
			_wxFlags = self._getWxFlags(alignment, borderFlags, layout)
			# If there are objects in this sizer already, add the default spacer
			if len(self.GetChildren()) > 0:
				self.addDefaultSpacer()
			if border is None:
				border = self.Border
			self.Add(item, proportion, _wxFlags, border)
			

	def insert(self, index, item, layout="normal", proportion=0, alignment=("top", "left"), 
		border=None, borderFlags=None):
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
		if type(layout) == int:
			# proportion was passed first
			layout, proportion = proportion, layout
			# in case layout wasn't specified
			if type(layout) == int:
				layout = "normal"
		
		if type(item) == tuple:
			# spacer
			self.Insert(index, item, proportion)
		else:
			# item is the window to add to the sizer
			_wxFlags = self._getWxFlags(alignment, borderFlags, layout)
			if border is None:
				border = self.Border
			# If there are objects in this sizer already, add the default spacer
			addSpacer = ( len(self.GetChildren()) > 0)
			self.Insert(index, item, proportion, _wxFlags, border)
			if addSpacer:
				self.addDefaultSpacer(index+1)


	
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
	
	
	def remove(self, item):
		"""This will remove the item from the sizer. It will not cause
		the item to be destroyed. If the item is not one of this sizer's
		items, no error will be raised - it will simply do nothing.
		"""
		self.Detach(item)
	
	
	def addSpacer(self, val, pos=None, proportion=0):
		if self.Orientation == "Vertical":
			spacer = (1, val)
		elif self.Orientation == "Horizontal":
			spacer = (val, 1)
		else:
			# Something's up; bail out
			return
		if pos is None:
			self.Add(spacer, proportion=proportion)
		else:
			self.Insert(pos, spacer, proportion=proportion)
	
	
	def appendSpacer(self, val, proportion=0):
		"""Appends a spacer to the sizer."""
		self.addSpacer(val, None, proportion)
	
	
	def insertSpacer(self, pos, val, proportion=0):
		"""Added to be consistent with the sizers' add/insert
		design. Inserts a spacer at the specified position.
		"""
		self.addSpacer(val, pos, proportion)
		
		
	def prependSpacer(self, val, proportion=0):
		"""Added to be consistent with the sizers' add/insert
		design. Inserts a spacer in the first position.
		"""
		self.addSpacer(val, 0, proportion=proportion)
		
		
	def addDefaultSpacer(self, pos=None):
		spc = self.Spacing
		if spc:
			self.addSpacer(spc, pos)
				
	
	def drawOutline(self, win, recurse=False):
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
		
		if recurse:
			for ch in self.GetChildren():
				if ch.IsSizer():
					ch.GetSizer().drawOutline(win, recurse)
				elif ch.IsWindow():
					try:
						w = ch.GetWindow()
						w.Sizer.drawOutline(w, True)
					except: pass
	
	
	def listMembers(self, recurse=False, lvl=0):
		"""Debugging method. This will list all the members of this sizer,
		and if recurse is True, drill down into all contained sizers.
		"""
		ret = ""
		indnt = "\t" * lvl
		for chl in self.GetChildren():
			ret += "SZITEM: %s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
					chl.GetBorder(), 
					chl.GetFlag(), 
					chl.GetMinSize(), 
					chl.GetPosition(), 
					chl.GetProportion(), 
					chl.GetRatio(), 
					chl.GetSize() )

			if chl.IsSizer():
				itm = chl.GetSizer()
				ret += "%s%s (%s)\n" % (indnt, itm.__class__, itm.Orientation)
				if recurse:
					try:
						ret += itm.listMembers(recurse=recurse, lvl=lvl+1)
					except:
						# not a Dabo sizer
						pass
			elif chl.IsWindow():
				itm = chl.GetWindow()
				try:
					ret += "%s%s (%s) - Pos:%s,%s - Size:%s,%s\n" % (indnt, 
							itm.Name, itm.__class__, itm.Left, itm.Top, itm.Width, itm.Height)
				except:
					# Not a Dabo instance
					ret += "%s%s\n" % (indnt, itm.__class__)
			elif chl.IsSpacer():
				itm = chl.GetSpacer()
				ret += "%sSpacer: W=%s, H=%s\n" % (indnt, itm.GetWidth(), itm.GetHeight())
		return ret
		
		
	def _getWxFlags(self, alignment, borderFlags, layout):
		# If alignment is passed as a single string instead of a tuple, 
		# convert it.
		if type(alignment) == str:
			alignment = (alignment, )
		if type(borderFlags) == str:
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

		if borderFlags is None:
			# Add any default borders. If no defaults set, set it to the default 'all'
			if self.BorderBottom:
				_wxFlags = _wxFlags | wx.BOTTOM
			if self.BorderLeft:
				_wxFlags = _wxFlags | wx.LEFT
			if self.BorderRight:
				_wxFlags = _wxFlags | wx.RIGHT
			if self.BorderTop:
				_wxFlags = _wxFlags | wx.TOP
			# Should we set the default?
			if not (self.BorderBottom or self.BorderLeft 
					or self.BorderRight or self.BorderTop):
				_wxFlags = _wxFlags | wx.ALL
		else:
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

		if layout.lower() in ("expand", "ex", "exp", "x", "grow"):
			_wxFlags = _wxFlags | wx.EXPAND
		elif layout.lower() == "fixed":
			_wxFlags = _wxFlags | wx.FIXED_MINSIZE

		return _wxFlags				


	def _getBorder(self):
		try:
			return self._border
		except:
			return 0
	def _setBorder(self, val):
		self._border = val
		
	def _getBorderBottom(self):
		try:
			return self._borderBottom
		except:
			return False
	def _setBorderBottom(self, val):
		self._borderBottom = val
		
	def _getBorderLeft(self):
		try:
			return self._borderLeft
		except:
			return False
	def _setBorderLeft(self, val):
		self._borderLeft = val
		
	def _getBorderRight(self):
		try:
			return self._borderRight
		except:
			return False
	def _setBorderRight(self, val):
		self._borderRight = val
		
	def _getBorderTop(self):
		try:
			return self._borderTop
		except:
			return False
	def _setBorderTop(self, val):
		self._borderTop = val
		
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
	
	def _getSpacing(self):
		try:
			return self._space
		except:
			# Default to zero
			return 0
	def _setSpacing(self, val):
		self._space = val
			
	def _getVisible(self):
		return self._visible
	def _setVisible(self, val):
		self._visible = val
		self.ShowItems(val)
	
	Border = property(_getBorder, _setBorder, None,
			"Sets the default border for the sizer.  (int)" )
	BorderBottom = property(_getBorderBottom, _setBorderBottom, None,
			"By default, do we add the border to the bottom side?  (bool)" )
	BorderLeft = property(_getBorderLeft, _setBorderLeft, None,
			"By default, do we add the border to the left side?  (bool)" )
	BorderRight = property(_getBorderRight, _setBorderRight, None,
			"By default, do we add the border to the right side?  (bool)" )
	BorderTop = property(_getBorderTop, _setBorderTop, None,
			"By default, do we add the border to the top side?  (bool)" )
	
	Orientation = property(_getOrientation, _setOrientation, None, 
		"Sets the orientation of the sizer, either 'Vertical' or 'Horizontal'.")

	Spacing = property(_getSpacing, _setSpacing, None, 
			"Amount of space automatically inserted between elements.  (int)")
			
	Visible = property(_getVisible, _setVisible, None, 
		"Shows/hides the sizer and its contained items  (bool)")
