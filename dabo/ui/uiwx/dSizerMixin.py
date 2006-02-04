import wx
import dabo
import dPemMixin
from dabo.dLocalize import _
from dabo.dObject import dObject


class dSizerMixin(dObject):
	"""Provides the interface for interacting with Sizers in Dabo.
	Many of the methods for adding objects to sizers take the 
	following parameters:
		layout: 
			"expand": The object will expand to fill in the extra space
				(may also use "ex" or simply "x" to mean the same thing)
			"fixed": The object will not be resized
			"normal": The sizer will determine how to lay out the object. (default)
		proportion: The relative space this object should get in relation to the 
			other objects. Default has all objects getting 0, equal share.
		halign, valign: Allows you to specify Horizontal and Vertical alignment
			independently. Alternately, you can specify both with a tuple passed
			to the 'alignment' parameter.
		alignment: The horizontal and vertical alignment of the object in the sizer.
			This is a tuple: set it like ("left", "top") or ("center", "middle"). In most
			cases, though, passing the separate halign and valign parameters
			is preferable.
		border: The width of the border. Default is 0, no border.
		borderSides: A tuple containing the locations to draw the border, such as
			("all") or ("top", "left", "bottom"). Default is ("all").
		index: The index of the existing sizer item before which you want
			the object inserted.
		For the most common usage of adding an object to the sizer, just do:
			sizer.append(object)
				or
			sizer.append(object, "x")
	"""
	# First, let's wrap some of the wx constants for those cases where
	# we need to work with them directly.
	horizontalFlag = wx.HORIZONTAL
	verticalFlag = wx.VERTICAL
	bothFlag = wx.BOTH
	leftFlag = wx.ALIGN_LEFT 
	rightFlag = wx.ALIGN_RIGHT
	centerFlag = wx.ALIGN_CENTER 
	centreFlag = wx.ALIGN_CENTER
	topFlag = wx.ALIGN_TOP 
	bottomFlag = wx.ALIGN_BOTTOM 
	middleFlag = wx.ALIGN_CENTER_VERTICAL
	borderBottomFlag = wx.BOTTOM
	borderLeftFlag = wx.LEFT
	borderRightFlag = wx.RIGHT 
	borderTopFlag = wx.TOP 
	borderAllFlag = wx.ALL 
	expandFlag = wx.EXPAND
	growFlag = wx.EXPAND
	fixedFlag = wx.FIXED_MINSIZE 
	# Also provide Dabo names for the sizer item classes
	SizerItem = wx.SizerItem
	GridSizerItem = wx.GBSizerItem

	
	
	def appendItems(self, items, *args, **kwargs):
		"""Append each item to the sizer."""
		ret = []
		for item in items:
			ret.append(self.append(item, *args, **kwargs))
		return ret
		
			
	def append(self, item, layout="normal", proportion=0, alignment=None,
			halign="left", valign="top", border=None, borderSides=None,
			borderFlags=None):
		"""Adds the passed object to the end of the list of items controlled
		by the sizer.
		"""
		if borderSides is None:
			if borderFlags is not None:
				dabo.errorLog.write(_("Depracation warning: use 'borderSides' parameter instead."))
				borderSides = borderFlags
		return self.insert(len(self.Children), item, layout=layout, proportion=proportion, 
				alignment=alignment, halign=halign, valign=valign, border=border, 
				borderSides=borderSides)
		

	def append1x(self, item, **kwargs):
		"""Shorthand for sizer.append(item, 1, "x"). """
		kwargs["layout"] = "expand"
		kwargs["proportion"] = 1
		return self.append(item, **kwargs)
		

	def insert(self, index, item, layout="normal", proportion=0, alignment=None,
			halign="left", valign="top", border=None, borderSides=None, 
			borderFlags=None):
		"""Inserts an object into the list of items controlled by the sizer at 
		the specified position. Sets that object's _controllingSizer and 
		_controllingSizerItem attributes.
		"""
		if borderSides is None:
			if borderFlags is not None:
				dabo.errorLog.write(_("Depracation warning: use 'borderSides' parameter instead."))
				borderSides = borderFlags
		if isinstance(layout, int):
			# proportion was passed first
			layout, proportion = proportion, layout
			# in case layout wasn't specified
			if isinstance(layout, int):
				layout = "normal"
		
		if isinstance(item, (int, tuple)):
			# spacer
			ret = self.addSpacer(item, pos=index, proportion=proportion)
		else:
			# item is the window to add to the sizer
			_wxFlags = self._getWxFlags(alignment, halign, valign, borderSides, layout)
			if border is None:
				border = self.Border
			# If there are objects in this sizer already, add the default spacer
			addSpacer = ( len(self.GetChildren()) > 0)
			ret = szItem = self.Insert(index, item, proportion=proportion, 
					flag=_wxFlags, border=border, userData=self)
			if addSpacer:
				self.addDefaultSpacer(index)
			item._controllingSizer = self
			item._controllingSizerItem = szItem
		return ret
		
	
	def layout(self):
		"""Layout the items in the sizer.
		This is handled automatically when the sizer is resized, but you'll have
		to call it manually after you are done adding items to the sizer.
		"""
		self.Layout()
		# Sizers only propagate down other sizers.  This will
		# cause all child panels to also re-calculate their layouts.
		for child in self.GetChildren():
			if child.IsWindow():
				try:
					child.GetWindow().layout()
				except: pass
	
	
	def prepend(self, *args, **kwargs):
		"""Insert the item at the beginning of the sizer layout."""
		return self.insert(0, *args, **kwargs)			
	
	
	def remove(self, item, destroy=None):
		"""This will remove the item from the sizer. It will not cause
		the item to be destroyed unless the 'destroy' parameter is True. 
		If the item is not one of this sizer's items, no error will be 
		raised - it will simply do nothing.
		"""
		try:
			item.Name
		except dabo.ui.deadObjectException:
			# The use of callAfter can sometimes result in destroyed
			# objects being removed.
			return
			
		self.Detach(item)
		item._controllingSizer = None
		item._controllingSizerItem = None
		if destroy:
			try:
				if isinstance(item, dabo.ui.dSizerMixin):
					item.release(True)
				else:
					item.release()
			except:
				item.Destroy()
	
	
	def addSpacer(self, val, pos=None, proportion=0):
		spacer = val
		if isinstance(val, int):
			if self.Orientation == "Vertical":
				spacer = (1, val)
			elif self.Orientation == "Horizontal":
				spacer = (val, 1)
			else:
				# Something's up; bail out
				return
		if pos is None:
			itm = self.Add(spacer, proportion=proportion, userData=self)
		else:
			itm = self.Insert(pos, spacer, proportion=proportion, userData=self)
		return itm
	
	
	def appendSpacer(self, val, proportion=0):
		"""Appends a spacer to the sizer."""
		return self.addSpacer(val, None, proportion)
	
	
	def insertSpacer(self, pos, val, proportion=0):
		"""Added to be consistent with the sizers' add/insert
		design. Inserts a spacer at the specified position.
		"""
		return self.addSpacer(val, pos, proportion)
		
		
	def prependSpacer(self, val, proportion=0):
		"""Added to be consistent with the sizers' add/insert
		design. Inserts a spacer in the first position.
		"""
		return self.addSpacer(val, 0, proportion=proportion)
		
		
	def addDefaultSpacer(self, pos=None):
		spc = self.Spacing
		if spc:
			self.addSpacer(spc, pos)
				
	
	def getItem(self, szItem):
		"""Querying sizers for their contents returns sizer items, not
		the actual items. So given a sizer item, this method will return
		the actual item in the sizer.
		"""
		ret = None
		if szItem is not None:
			if szItem.IsWindow():
				ret = szItem.GetWindow()
			elif szItem.IsSpacer():
				ret = szItem.GetSpacer()
			elif szItem.IsSizer():
				ret = szItem.GetSizer()
		return ret	
	
	
	def release(self, releaseContents=False):
		"""Normally just destroys the sizer, leaving any objects
		controlled by the sizer intact. But if the 'releaseContents'
		parameter is passed as True, all objects contained in the
		sizer are destroyed first.
		"""
		if releaseContents:
			for szItem in self.GetChildren():
				if szItem.IsWindow():
					itm = szItem.GetWindow()
					self.remove(itm, True)
				elif szItem.IsSpacer():
					# Spacers will be destroyed when the sizer is destroyed
					pass
				elif szItem.IsSizer():
					szr = szItem.GetSizer()
					self.remove(szr, True)
		# Release this sizer
		if isinstance(self, dabo.ui.dBorderSizer):
			dabo.ui.callAfter(self.Box.release)
		self.Destroy()
	
	
	def getPositionInSizer(self):
		""" Returns the current position of this sizer in its containing sizer."""
		sz = self._controllingSizer
		if not sz:
			return None
		if isinstance(sz, wx.BoxSizer):
			children = sz.GetChildren()
			for pos, szitem in enumerate(children):
				if szitem.IsSizer():
					if szitem.GetSizer() == self:
						return pos
			# If we reached here, something's wrong!
			dabo.errorLog.write(_("Containing sizer did not match item %s") % self.Name)
			return None
		elif isinstance(sz, wx.GridBagSizer):
			# Return a row,col tuple
			row, col = sz.GetItemPosition(self)
			return (row, col)
		else:
			return None
	
	
	def showItem(self, itm):
		"""Makes sure that the passed item is visible"""
		self.Show(itm, show=True, recursive=True)
		self.layout()
		
		
	def hideItem(self, itm):
		"""Hides the passed item"""
		self.Show(itm, show=False, recursive=True)
		self.layout()


	def getItemProp(self, itm, prop):
		"""Get the current value of the specified property for the sizer item.
		Grid sizers must override with their specific props.
		"""
		if prop == "Border":
			return itm.GetBorder()
		elif prop == "Proportion":
			return itm.GetProportion()
		else:
			# Property is in the flag setting.
			flag = itm.GetFlag()
			szClass = dabo.ui.dSizer
			if prop == "Expand":
				return bool(flag & szClass.expandFlag)
			elif prop == "Halign":
				if flag & szClass.rightFlag:
					return "Right"
				elif flag & szClass.centerFlag:
					return "Center"
				else: 		#if flag & szClass.leftFlag:
					return "Left"
			elif prop == "Valign":
				if flag & szClass.middleFlag:
					return "Middle"
				elif flag & szClass.bottomFlag:
					return "Bottom"
				else:		#if flag & szClass.topFlag:
					return "Top"
			elif prop == "BorderSides":
				pdBorder = {"Bottom" : self.borderBottomFlag,
						"Left" : self.borderLeftFlag,
						"Right" : self.borderRightFlag, 
						"Top" : self.borderTopFlag}
				if flag & self.borderAllFlag:
					return ["All"]
				ret = []
				for side, val in pdBorder.items():
					if flag and val:
						ret.append(key)
				if not ret:
					ret = ["None"]
				return ret
	
	
	def setItemProp(self, itm, prop, val):
		"""Given a sizer item, a property and a value, sets things as you
		would expect. 
		"""
		if val is None:
			return
		ret = False
		lowprop = prop.lower()
		if isinstance(itm, self.GridSizerItem):
			row, col = self.getGridPos(itm)
		if lowprop == 'proportion':
			itm.SetProportion(int(val))
			ret = True
		elif lowprop == "border":
			itm.SetBorder(int(val))
			ret = True
		elif lowprop == "rowexpand" and isinstance(self, dabo.ui.dGridSizer):
			self.setRowExpand(val, row)
			ret = True
		elif lowprop == "colexpand" and isinstance(self, dabo.ui.dGridSizer):
			self.setColExpand(val, col)			
			ret = True
		elif lowprop in ("expand", "halign", "valign", "bordersides"):
			ret = True
			pd = {"left" : self.leftFlag, 
					"right" : self.rightFlag,
					"center" : self.centerFlag, 
					"centre" : self.centreFlag,
					"top" : self.topFlag, 
					"bottom" : self.bottomFlag, 
					"middle" : self.middleFlag,
					"expand" : self.expandFlag,
					"grow" : self.expandFlag,
					"fixed" : self.fixedFlag }	
			pdBorder = {"bottom" : self.borderBottomFlag,
					"left" : self.borderLeftFlag,
					"right" : self.borderRightFlag, 
					"top" : self.borderTopFlag, 
					"all" : self.borderAllFlag }
			flg = itm.GetFlag()
			if lowprop == "expand":
				xFlag = pd["expand"]
				if val:
					flg = flg | xFlag
				else:
					flg = flg & ~xFlag
			elif lowprop in ("halign", "valign"):
				opts = {"halign" : ("left", "center", "right"),
						"valign" : ("top", "middle", "bottom")}[lowprop]
				vallow = val.lower()
				for opt in opts:
					if opt == vallow:
						flg = flg | pd[opt]
					else:
						flg = flg & ~pd[opt]
			elif lowprop == ("bordersides"):
				if val is None:
					return
				if isinstance(val, basestring):
					val = [val]
				lowval = [vv.lower() for vv in val]
				if "all" in lowval:
					flg = flg | pdBorder["all"]
				else:
					for opt in pdBorder:
						if opt == "all":
							continue
						xFlag = pdBorder[opt]
						if opt in lowval:
							flg = flg | xFlag
						else:
							flg = flg & ~xFlag

			itm.SetFlag(flg)
		try:
			self.Parent.layout()
		except:
			self.layout()
		return ret
	

	def setItemProps(self, itm, props):
		"""This accepts a dict of properties and values, and
		applies them to the specified sizer item.
		"""
		for prop, val in props.items():
			self.setItemProp(itm, prop, val)
	

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
		# Pen Width
		pw = 1
		if self.Application.Platform == "Win":
			# Make 'em a bit wider.
			pw = 3
		
		dc = wx.ClientDC(win)
		dc.SetPen(wx.Pen(self.outlineColor, pw, wx.SHORT_DASH))
		dc.SetBrush(wx.TRANSPARENT_BRUSH)
		dc.SetLogicalFunction(wx.COPY)
		# Draw the outline
		dabo.ui.callAfter(dc.DrawRectangle, x+off, y+off, w-(2*off), h-(2*off) )
		
		if recurse:
			for ch in self.GetChildren():
				if ch.IsSizer():
					sz = ch.GetSizer()
					if hasattr(sz, "drawOutline"):
						sz.drawOutline(win, recurse)
				elif ch.IsWindow():
					w = ch.GetWindow()
					if isinstance(w, dabo.ui.dPageFrame):
						w = w.SelectedPage
					if hasattr(w, "Sizer") and w.Sizer:	
						w.Sizer.drawOutline(w, True)

	
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
		
		
	def _getWxFlags(self, alignment, halign, valign, borderSides, layout):
		"""This converts Dabo values for sizer control into wx-specific constants."""
		# Begin with the constant for no flag values.
		_wxFlags = 0

		if alignment is not None:
			# User passed an individual alignment tuple. Use that instead of
			# the separate halign and valign values.
			# If alignment is passed as a single string instead of a tuple, 
			# convert it.
			if isinstance(alignment, basestring):
				alignFlags = (alignment, )
			else:
				alignFlags = alignment
		else:
			# Use the halign and valign values
			alignFlags = (halign, valign)
		for flag in [flag.lower() for flag in alignFlags]:
			if flag == "left":
				_wxFlags = _wxFlags | self.leftFlag
			elif flag == "right":
				_wxFlags = _wxFlags | self.rightFlag
			elif flag in ("center", "centre"):
				_wxFlags = _wxFlags | self.centerFlag
			elif flag == "top":
				_wxFlags = _wxFlags | self.topFlag
			elif flag == "bottom":
				_wxFlags = _wxFlags | self.bottomFlag
			elif flag == "middle":
				_wxFlags = _wxFlags | self.middleFlag

		if isinstance(borderSides, basestring):
			borderSides = (borderSides, )
		if borderSides is None:
			# Add any default borders. If no defaults set, set it to the default 'all'
			if self.BorderBottom:
				_wxFlags = _wxFlags | self.borderBottomFlag
			if self.BorderLeft:
				_wxFlags = _wxFlags | self.borderLeftFlag
			if self.BorderRight:
				_wxFlags = _wxFlags | self.borderRightFlag
			if self.BorderTop:
				_wxFlags = _wxFlags | self.borderTopFlag
			# Should we set the default?
			if not (self.BorderBottom or self.BorderLeft 
					or self.BorderRight or self.BorderTop):
				_wxFlags = _wxFlags | self.borderAllFlag
		else:
			for flag in [flag.lower() for flag in borderSides]:
				if flag == "left":
					_wxFlags = _wxFlags | self.borderLeftFlag
				elif flag == "right":
					_wxFlags = _wxFlags | self.borderRightFlag
				elif flag == "top":
					_wxFlags = _wxFlags | self.borderTopFlag
				elif flag == "bottom":
					_wxFlags = _wxFlags | self.borderBottomFlag
				elif flag == "all":
					_wxFlags = _wxFlags | self.borderAllFlag

		if layout.lower() in ("expand", "ex", "exp", "x", "grow"):
			_wxFlags = _wxFlags | self.expandFlag
		elif layout.lower() == "fixed":
			_wxFlags = _wxFlags | self.fixedFlag

		return _wxFlags				


	def _getBorder(self):
		try:
			return self._border
		except:
			return 0
			
	def _setBorder(self, val):
		if isinstance(val, basestring):
			val = int(val)
		self._border = val
		
		
	def _getBorderAll(self):
		try:
			return (self._borderBottom and self._borderTop
					and self._borderLeft and self._borderRight )
		except:
			return False
			
	def _setBorderAll(self, val):
		if isinstance(val, basestring):
			val = (val.lower()[0] in ("t", "y"))
		self._borderBottom = self._borderTop = self._borderLeft = self._borderRight = val
		
		
	def _getBorderBottom(self):
		try:
			return self._borderBottom
		except:
			return False
			
	def _setBorderBottom(self, val):
		if isinstance(val, basestring):
			val = (val.lower()[0] in ("t", "y"))
		self._borderBottom = val
		
		
	def _getBorderLeft(self):
		try:
			return self._borderLeft
		except:
			return False
			
	def _setBorderLeft(self, val):
		if isinstance(val, basestring):
			val = (val.lower()[0] in ("t", "y"))
		self._borderLeft = val
		
		
	def _getBorderRight(self):
		try:
			return self._borderRight
		except:
			return False
			
	def _setBorderRight(self, val):
		if isinstance(val, basestring):
			val = (val.lower()[0] in ("t", "y"))
		self._borderRight = val
		
		
	def _getBorderTop(self):
		try:
			return self._borderTop
		except:
			return False
			
	def _setBorderTop(self, val):
		if isinstance(val, basestring):
			val = (val.lower()[0] in ("t", "y"))
		self._borderTop = val
	
	
	def _getChildren(self):
		ret = self.GetChildren()
		for itm in ret:
			itm.ControllingSizer = self
		return ret
	
	
	def _getChildWindows(self):
		itms = self.GetChildren()
		ret = [itm.GetWindow()
				for itm in itms
				if itm.IsWindow() ]
		return ret
	
	
	def _getCntrlSizer(self):
		try:
			ret = self._controllingSizer
		except:
			ret = self._controllingSizer = None
		return ret
		
		
	def _getCntrlSzItem(self):
		try:
			ret = self._controllingSizerItem
		except:
			ret = self._controllingSizerItem = None
		return ret
		

	def _getHt(self):
		return self.GetSize()[1]
		
		
	def _getOrientation(self):
		o = self.GetOrientation()
		if o == self.verticalFlag:
			return "Vertical"
		elif o == self.horizontalFlag:
			return "Horizontal"
		else:
			return "?"
			
	def _setOrientation(self, val):
		if val[0].lower() == "v":
			self.SetOrientation(self.verticalFlag)
		else:
			self.SetOrientation(self.horizontalFlag)
	
	
	def _getParent(self):
		ret = self._parent
		ob = self
		while ret is None:
			# Nested sizers need to traverse their containing
			# sizers to find the parent object
			cs = ob.ControllingSizer
			if cs is None:
				# Something's wrong!
				dabo.errorLog.write(_("Nested sizer missing its ControllingSizer"))
				break
			else:
				ob = cs
				ret = ob._parent 
		return ret
		
	def _setParent(self, obj):
		self._parent = obj
					
		
	def _getSpacing(self):
		try:
			return self._space
		except:
			# Default to zero
			return 0
			
	def _setSpacing(self, val):
		if isinstance(val, basestring):
			val = int(val)
		self._space = val
		
			
	def _getVisible(self):
		return self._visible
		
	def _setVisible(self, val):
		if isinstance(val, basestring):
			val = (val.lower()[0] in ("t", "y"))
		self._visible = val
		self.ShowItems(val)
		
	
	def _getWd(self):
		return self.GetSize()[0]		
		
	
	Border = property(_getBorder, _setBorder, None,
			_("Sets the default border for the sizer.  (int)" ) )
			
	BorderAll = property(_getBorderAll, _setBorderAll, None,
			_("By default, do we add the border to all sides?  (bool)" ) )
			
	BorderBottom = property(_getBorderBottom, _setBorderBottom, None,
			_("By default, do we add the border to the bottom side?  (bool)" ) )
			
	BorderLeft = property(_getBorderLeft, _setBorderLeft, None,
			_("By default, do we add the border to the left side?  (bool)" ) )
			
	BorderRight = property(_getBorderRight, _setBorderRight, None,
			_("By default, do we add the border to the right side?  (bool)" ) )
			
	BorderTop = property(_getBorderTop, _setBorderTop, None,
			_("By default, do we add the border to the top side?  (bool)" ) )

	Children = property(_getChildren, None, None, 
			_("List of all the sizer items managed by this sizer  (list of sizerItems" ) )
	
	ChildWindows = property(_getChildWindows, None, None, 
			_("List of all the windows that are directly managed by this sizer  (list of controls" ) )
	
	ControllingSizer = property(_getCntrlSizer, None, None,
			_("""Reference to the sizer that controls this control's layout.  (dSizer)""") )

	ControllingSizerItem = property(_getCntrlSzItem, None, None,
			_("""Reference to the sizer item that control's this control's layout.
				This is useful for getting information about how the item is being 
				sized, and for changing those settings."""))
		
	Height = property(_getHt, None, None,
			_("Height of the sizer  (int)") )
			
	Orientation = property(_getOrientation, _setOrientation, None, 
			_("Sets the orientation of the sizer, either 'Vertical' or 'Horizontal'." ) )

	Parent = property(_getParent, _setParent, None,	
			_("""The object that contains this sizer. In the case of nested
			sizers, it is the object that the outermost sizer belongs to. (obj)"""))
	
	Spacing = property(_getSpacing, _setSpacing, None, 
			_("Amount of space automatically inserted between elements.  (int)" ) )
			
	Visible = property(_getVisible, _setVisible, None, 
			_("Shows/hides the sizer and its contained items  (bool)" ) )

	Width = property(_getWd, None, None,
			_("Width of this sizer  (int)") )

