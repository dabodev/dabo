# -*- coding: utf-8 -*-
import wx
import dabo
import dPemMixin
from dabo.dLocalize import _
from dabo.dObject import dObject
from dabo.ui import makeDynamicProperty

class dSizerMixin(dObject):
	"""
	Provides the interface for interacting with Sizers in Dabo.
	"""
	# Additional documentation for several of the contained methods:
	_doc_additions = """

		+--------------------------------------------------------------------------+
		|Additional arguments:                                                     |
		+=============+============================================================+
		|layout:      |Specifies how the object expands in the opposite dimension  |
		|             |of the sizer. If "normal" (the default), no expansion takes |
		|             |place. If "expand" (a common setting), the item will expand |
		|             |to fill up otherwise unoccupied space in the sizer.         |
		+-------------+------------------------------------------------------------+
		|proportion   |Specifies the proportional amount of space that the object  |
		|             |can grow to in the same dimension as this sizer. If 0 (the  |
		|             |default), the object will maintain its size. If > 0, the    |
		|             |object will get a spacing in the sizer proportional to      |
		|             |other objects in the sizer with proportions > 0. So if this |
		|             |is a horizontal sizer, and the proportion for the object is |
		|             |set to 1, and no other objects in the sizer have proportion |
		|             |set, the object will fill up all extra horizontal space.    |
		+-------------+------------------------------------------------------------+
		|alignment    |Possible values are "top", "middle", and "bottom" for       |
		|             |horizontal sizers, and "left", "center", and "right" for    |
		|             |vertical sizers. Specifies where the object appears within  |
		|             |the available area in the sizer.                            |
		+-------------+------------------------------------------------------------+
		|halign       |Only used if the alignment property not set.                |
		+-------------+------------------------------------------------------------+
		|valign       |Only used if the alignment property not set.                |
		+-------------+------------------------------------------------------------+
		|border       |Specifies the number of pixels to put around the object in  |
		|             |the sizer, on the sides specified by the borderSides        |
		|             |argument, or by the value of the DefaultBorderLeft,         |
		|             |DefaultBorderRight, DefaultBorderTop, and                   |
		|             |DefaultBorderBottom boolean properties.                     |
		+-------------+------------------------------------------------------------+
		|borderSides  |Specifies the sides around the object to place the border   |
		|             |specified in the border argument or the DefaultBorder       |
		|             |property. This should be a tuple that contains at least     |
		|             |some of the values ("left", "right", "top", "bottom")       |
		+-------------+------------------------------------------------------------+
"""

	# First, let's wrap some of the wx constants for those cases where
	# we need to work with them directly.
	horizontalFlag = wx.HORIZONTAL
	verticalFlag = wx.VERTICAL
	bothFlag = wx.BOTH
	leftFlag = wx.ALIGN_LEFT
	rightFlag = wx.ALIGN_RIGHT
	centerFlag = wx.ALIGN_CENTER_HORIZONTAL
	centreFlag = wx.ALIGN_CENTER_HORIZONTAL
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
	shapedFlag = wx.SHAPED
	fixedFlag = wx.FIXED_MINSIZE
	# Also provide Dabo names for the sizer item classes
	SizerItem = wx.SizerItem
	GridSizerItem = wx.GBSizerItem


	def __init__(self, *args, **kwargs):
		super(dSizerMixin, self).__init__(*args, **kwargs)


	def _afterInit(self):
		self.outlineColor = self.outlineStyle = self.outlineWidth = None
		super(dSizerMixin, self)._afterInit()


	def appendItems(self, items, *args, **kwargs):
		"""Append each item to the sizer."""
		ret = []
		for itm in items:
			ret.append(self.append(itm, *args, **kwargs))
		return ret
	try:
		appendItems.__doc__ += _doc_additions
	except TypeError:
		# If compressed to .pyo, __doc__ will be None.
		pass


	def append(self, obj, layout="normal", proportion=0, alignment=None,
			halign="left", valign="top", border=None, borderSides=None):
		"""Adds the passed object to the end of the sizer layout."""
		return self.insert(len(self.Children), obj, layout=layout, proportion=proportion,
				alignment=alignment, halign=halign, valign=valign, border=border,
				borderSides=borderSides)
	try:
		append.__doc__ += _doc_additions
	except TypeError:
		# If compressed to .pyo, __doc__ will be None.
		pass

	def append1x(self, obj, **kwargs):
		"""Shorthand for sizer.append(obj, 1, "expand")."""
		kwargs["layout"] = "expand"
		kwargs["proportion"] = 1
		return self.append(obj, **kwargs)


	def insert(self, index, obj, layout="normal", proportion=0, alignment=None,
			halign="left", valign="top", border=None, borderSides=None):
		"""Inserts the passed object into the sizer layout at the specified position."""
		if obj in self.ChildSizers:
			raise ValueError, _("Adding the same sizer twice is not allowed.")
		if isinstance(layout, int):
			# proportion was passed first
			layout, proportion = proportion, layout
			# in case layout wasn't specified
			if isinstance(layout, int):
				layout = "normal"

		if isinstance(obj, (int, tuple)):
			# obj is a spacer
			ret = self.addSpacer(obj, pos=index, proportion=proportion)
		else:
			# obj is the window to add to the sizer
			_wxFlags = self._getWxFlags(alignment, halign, valign, borderSides, layout)
			if border is None:
				border = self.DefaultBorder
			# If there are objects in this sizer already, add the default spacer
			addSpacer = ( len(self.GetChildren()) > 0)
			ret = szItem = self.Insert(index, obj, proportion=proportion,
					flag=_wxFlags, border=border, userData=self)
			if addSpacer:
				self.addDefaultSpacer(index)
			obj._controllingSizer = self
			obj._controllingSizerItem = szItem
			if ret.IsSizer():
				obj._parent = self._parent
		return ret
	try:
		insert.__doc__ += _doc_additions
	except TypeError:
		# If compressed to .pyo, __doc__ will be None.
		pass


	def layout(self):
		"""
		Layout the items in the sizer.

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
				except AttributeError:
					pass


	def prepend(self, obj, layout="normal", proportion=0, alignment=None,
			halign="left", valign="top", border=None, borderSides=None):
		"""Insert the object at the beginning of the sizer layout."""
		return self.insert(0, obj, layout=layout, proportion=proportion,
				alignment=alignment, halign=halign, valign=valign, border=border,
				borderSides=borderSides)
	try:
		prepend.__doc__ += _doc_additions
	except TypeError:
		# If compressed to .pyo, __doc__ will be None.
		pass


	def remove(self, itm, destroy=None):
		"""
		This will remove the item from the sizer. It will not cause
		the item to be destroyed unless the 'destroy' parameter is True.
		If the item is not one of this sizer's items, no error will be
		raised - it will simply do nothing.
		"""
		try:
			itm.Name
		except dabo.ui.deadObjectException:
			# The use of callAfter can sometimes result in destroyed
			# objects being removed.
			return
		if self.Detach(itm):
			itm._controllingSizer = None
			itm._controllingSizerItem = None
			if destroy:
				try:
					if isinstance(itm, dabo.ui.dSizerMixin):
						itm.release(True)
					else:
						itm.release()
				except AttributeError:
					itm.Destroy()


	def clear(self, destroy=False):
		"""
		This method is called to remove all items from the sizer. If the
		optional 'destroy' parameter is set to True, any contained items
		will be destroyed. Otherwise, they will remain as is, but no longer
		under control of the sizer.
		"""
		self.Clear(destroy)


	def addSpacer(self, val, pos=None, proportion=0):
		spacer = val
		if isinstance(val, int):
			if self.Orientation == "Vertical":
				spacer = (0, val)
			else:
				spacer = (val, 0)
		if pos is None:
			itm = self.Add(spacer, proportion=proportion, userData=self)
		else:
			itm = self.Insert(pos, spacer, proportion=proportion, userData=self)
		itm.setSpacing = itm.SetSpacer
		return itm


	def appendSpacer(self, val, proportion=0):
		"""Appends a spacer to the sizer."""
		return self.addSpacer(val, None, proportion)


	def insertSpacer(self, pos, val, proportion=0):
		"""
		Added to be consistent with the sizers' add/insert
		design. Inserts a spacer at the specified position.
		"""
		return self.addSpacer(val, pos, proportion)


	def prependSpacer(self, val, proportion=0):
		"""
		Added to be consistent with the sizers' add/insert
		design. Inserts a spacer in the first position.
		"""
		return self.addSpacer(val, 0, proportion=proportion)


	def addDefaultSpacer(self, pos=None):
		spc = self.DefaultSpacing
		if spc and not hasattr(self, "isDesignerSizer"):
			# Don't add default spacers in the Designer
			self.addSpacer(spc, pos)


	def getItem(self, szItem):
		"""
		Querying sizers for their contents returns sizer items, not
		the actual items. So given a sizer item, this method will return
		the actual item in the sizer.
		"""
		ret = None
		if szItem is not None:
			if szItem.IsWindow():
				ret = szItem.GetWindow()
			elif szItem.IsSpacer():
				ret = szItem.GetSpacer()
				ret._controllingSizerItem = szItem
				ret._controllingSizer = self
			elif szItem.IsSizer():
				ret = szItem.GetSizer()
		return ret


	def release(self, releaseContents=False):
		"""
		Normally just destroys the sizer, leaving any objects
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
		"""
		Returns the current position of this sizer in its containing sizer, or None
		if there isn't a containing sizer.
		"""
		sz = getattr(self, "_controllingSizer", None)
		if not sz:
			return None
		if isinstance(sz, wx.BoxSizer):
			children = sz.GetChildren()
			for pos, szitem in enumerate(children):
				if szitem.IsSizer():
					if szitem.GetSizer() == self:
						return pos
			# If we reached here, something's wrong!
			dabo.log.error(_("Containing sizer did not match item %s") % self.Name)
			return None
		elif isinstance(sz, wx.GridBagSizer):
			# Return a row,col tuple
			row, col = sz.GetItemPosition(self)
			return (row, col)
		else:
			return None


	def setPositionInSizer(self, obj, pos):
		orig_pos = obj.getPositionInSizer()
		# Copy the current sizer props
		props = self.getItemProps(obj)
		if isinstance(self, wx.BoxSizer):
			self.remove(obj)
			self.insert(pos, obj)
			self.setItemProps(obj, props)
		elif isinstance(self, wx.GridBagSizer):
			row, col = pos
			if self.getItemByRowCol(row, col):
				raise ValueError(_("An object already exists at %(row)s, "
						"%(col)s") % locals())
			self.remove(obj)
			self.append(obj, row=row, col=col)
			self.setItemProps(obj, props)
		self.layout()


	def showItem(self, itm):
		"""Makes sure that the passed item is visible"""
		self.Show(itm, show=True, recursive=True)
		self.layout()


	def hideItem(self, itm):
		"""Hides the passed item"""
		self.Show(itm, show=False, recursive=True)
		self.layout()


	def getItemProps(self, itm):
		"""
		Returns a dict containing all the sizer properties as keys along with
		their associated values.
		"""
		propNames = ("Border", "BorderSides", "ColSpan", "Expand", "HAlign",
				"Proportion", "RowSpan", "VAlign")
		return dict([(prop, self.getItemProp(itm, prop)) for prop in propNames])


	def getItemProp(self, itm, prop):
		"""
		Get the current value of the specified property for the sizer item.
		Grid sizers must override with their specific props.
		"""
		lowprop = prop.lower()
		if not isinstance(itm, (self.SizerItem, self.GridSizerItem)):
			itm = itm.ControllingSizerItem
		if lowprop == "border":
			return itm.GetBorder()
		elif lowprop == "proportion":
			return itm.GetProportion()
		else:
			# Property is in the flag setting.
			flag = itm.GetFlag()
			szClass = dabo.ui.dSizer
			if lowprop == "expand":
				return bool(flag & szClass.expandFlag)
			elif lowprop == "halign":
				if flag & szClass.rightFlag:
					return "Right"
				elif flag & szClass.centerFlag:
					return "Center"
				else: 		#if flag & szClass.leftFlag:
					return "Left"
			elif lowprop == "valign":
				if flag & szClass.middleFlag:
					return "Middle"
				elif flag & szClass.bottomFlag:
					return "Bottom"
				else:		#if flag & szClass.topFlag:
					return "Top"
			elif lowprop == "bordersides":
				pdBorder = {"Bottom" : self.borderBottomFlag,
						"Left" : self.borderLeftFlag,
						"Right" : self.borderRightFlag,
						"Top" : self.borderTopFlag}
				if flag & self.borderAllFlag == self.borderAllFlag:
					return ["All"]
				ret = []
				for side, val in pdBorder.items():
					if flag & val:
						ret.append(side)
				if not ret:
					ret = ["None"]
				return ret


	def setItemProp(self, itm, prop, val):
		"""
		Given a sizer item, a property and a value, sets things as you
		would expect.
		"""
		if not itm:
			return
		if not isinstance(itm, (self.SizerItem, self.GridSizerItem)):
			itm = itm.ControllingSizerItem
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
			if itm.GetBorder() != int(val):
				itm.SetBorder(int(val))
			ret = True
		elif lowprop == "rowexpand" and isinstance(self, dabo.ui.dGridSizer):
			self.setRowExpand(val, row)
			ret = True
		elif lowprop == "colexpand" and isinstance(self, dabo.ui.dGridSizer):
			self.setColExpand(val, col)
			ret = True
		elif lowprop == "rowspan" and isinstance(self, dabo.ui.dGridSizer):
			ret = self.setRowSpan(itm, val)
		elif lowprop == "colspan" and isinstance(self, dabo.ui.dGridSizer):
			ret = self.setColSpan(itm, val)
		elif lowprop == "spacing":
			if isinstance(val, int):
				val = (val, val)
			elif isinstance(val, basestring):
				val = (int(val), int(val))
			try:
				ret = itm.SetSpacer(val)
				ret = True
			except AttributeError:
				pass
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
				# Clear the 'all' flag
				flg = flg & ~pdBorder["all"]
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
			itm = self.Parent
		except AttributeError:
			itm = self
		dabo.ui.callAfterInterval(50, self._safeLayout, itm)
		return ret


	def setItemProps(self, itm, props):
		"""
		This accepts a dict of properties and values, and
		applies them to the specified sizer item.
		"""
		for prop, val in props.items():
			if itm:
				self.setItemProp(itm, prop, val)


	def _safeLayout(self, itm):
		if not itm:
			return
		try:
			itm.layout()
		except AttributeError:
			pass


	def isContainedBy(self, obj):
		"""
		Returns True if this the containership hierarchy for this control
		includes obj.
		"""
		ret = False
		p = self.Parent
		while p is not None:
			if p is obj:
				ret = True
				break
			else:
				p = p.Parent
		return ret


	@dabo.ui.deadCheck
	def getContainingWindow(self):
		"""
		Return the window that contains this sizer. In the case of nested
		sizers, traverse the parent hierarchy until a window is reached.
		"""
		ret = self.Parent
		while ret and isinstance(ret, dSizerMixin):
			ret = ret.Parent
		return ret


	def _resolveOutlineSettings(self):
		if self.outlineColor is None:
			if self.Orientation == "Vertical":
				self.outlineColor = wx.BLUE
			else:
				self.outlineColor = wx.RED
		else:
			if isinstance(self.outlineColor, basestring):
				# translate to a wx.Colour
				self.outlineColor = wx.NamedColour(self.outlineColor)
		if self.outlineWidth is None:
			if self.Application.Platform == "Win":
				# Make 'em a bit wider.
				self.outlineWidth = 3
			else:
				self.outlineWidth = 1
		if self.outlineStyle is None:
			self.outlineStyle = wx.SHORT_DASH
		else:
			if isinstance(self.outlineStyle, basestring):
				sty = self.outlineStyle.lower()
				if sty == "dot":
					self.outlineStyle = wx.DOT
				elif sty == "dash":
					self.outlineStyle = wx.SHORT_DASH
				elif sty == "solid":
					self.outlineStyle = wx.SOLID


	def drawOutline(self, win, recurse=False, drawChildren=False):
		"""
		There are some cases where being able to see the sizer
		is helpful, such as at design time. This method can be called
		to see the outline; it needs to be called whenever the containing
		window is resized or repainted.
		"""
		self._resolveOutlineSettings()
		if drawChildren:
			objs = self.GetChildren()
		else:
			objs = [self]
		for obj in objs:
			x, y = obj.GetPosition()
			w, h = obj.GetSize()
			# Offset
			off = (self.outlineWidth / 2)
			dc = wx.ClientDC(win)
			dc.SetPen(wx.Pen(self.outlineColor, self.outlineWidth, self.outlineStyle))
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
		"""
		Debugging method. This will list all the members of this sizer,
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
					except AttributeError:
						# not a Dabo sizer
						pass
			elif chl.IsWindow():
				itm = chl.GetWindow()
				try:
					ret += "%s%s (%s) - Pos:%s,%s - Size:%s,%s\n" % (indnt,
							itm.Name, itm.__class__, itm.Left, itm.Top, itm.Width, itm.Height)
				except AttributeError:
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
			if self.DefaultBorderBottom:
				_wxFlags = _wxFlags | self.borderBottomFlag
			if self.DefaultBorderLeft:
				_wxFlags = _wxFlags | self.borderLeftFlag
			if self.DefaultBorderRight:
				_wxFlags = _wxFlags | self.borderRightFlag
			if self.DefaultBorderTop:
				_wxFlags = _wxFlags | self.borderTopFlag
			# Should we set the default?
			if not (self.DefaultBorderBottom or self.DefaultBorderLeft
					or self.DefaultBorderRight or self.DefaultBorderTop):
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
		elif layout.lower() == "shaped":
			_wxFlags = _wxFlags | self.shapedFlag
		elif layout.lower() == "fixed":
			_wxFlags = _wxFlags | self.fixedFlag

		return _wxFlags



	def _getChildren(self):
		ret = self.GetChildren()
		for itm in ret:
			itm.ControllingSizer = self
		return ret


	def _getChildSpacers(self):
		itms = self.GetChildren()
		ret = [itm for itm in itms
				if itm.IsSpacer() ]
		return ret


	def _getChildObjects(self):
		itms = self.GetChildren()
		ret = [self.getItem(itm) for itm in itms]
		return ret


	def _getChildSizers(self):
		itms = self.GetChildren()
		ret = [itm.GetSizer()
				for itm in itms
				if itm.IsSizer() ]
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
		except AttributeError:
			ret = self._controllingSizer = None
		return ret


	def _getCntrlSzItem(self):
		try:
			ret = self._controllingSizerItem
		except AttributeError:
			ret = self._controllingSizerItem = None
		return ret


	def _getDefaultBorder(self):
		try:
			return self._defaultBorder
		except AttributeError:
			ret = self._defaultBorder = 0
			return ret

	def _setDefaultBorder(self, val):
		if isinstance(val, basestring):
			val = int(val)
		self._defaultBorder = val


	def _getDefaultBorderAll(self):
		try:
			return (self._defaultBorderBottom and self._defaultBorderTop
					and self._defaultBorderLeft and self._defaultBorderRight )
		except AttributeError:
			return False

	def _setDefaultBorderAll(self, val):
		if isinstance(val, basestring):
			val = (val.lower()[0] in ("t", "y"))
		self._defaultBorderBottom = self._defaultBorderTop = \
				self._defaultBorderLeft = self._defaultBorderRight = val


	def _getDefaultBorderBottom(self):
		try:
			return self._defaultBorderBottom
		except AttributeError:
			ret = self._defaultBorderBottom = False
			return ret

	def _setDefaultBorderBottom(self, val):
		if isinstance(val, basestring):
			val = (val.lower()[0] in ("t", "y"))
		self._defaultBorderBottom = val


	def _getDefaultBorderLeft(self):
		try:
			return self._defaultBorderLeft
		except AttributeError:
			ret = self._defaultBorderLeft = False
			return ret

	def _setDefaultBorderLeft(self, val):
		if isinstance(val, basestring):
			val = (val.lower()[0] in ("t", "y"))
		self._defaultBorderLeft = val


	def _getDefaultBorderRight(self):
		try:
			return self._defaultBorderRight
		except AttributeError:
			ret = self._defaultBorderRight = False
			return ret

	def _setDefaultBorderRight(self, val):
		if isinstance(val, basestring):
			val = (val.lower()[0] in ("t", "y"))
		self._defaultBorderRight = val


	def _getDefaultBorderTop(self):
		try:
			return self._defaultBorderTop
		except AttributeError:
			ret = self._defaultBorderTop = False
			return ret

	def _setDefaultBorderTop(self, val):
		if isinstance(val, basestring):
			val = (val.lower()[0] in ("t", "y"))
		self._defaultBorderTop = val


	def _getDefaultSpacing(self):
		try:
			return self._defaultSpacing
		except AttributeError:
			ret = self._defaultSpacing = 0
			return ret

	def _setDefaultSpacing(self, val):
		if isinstance(val, basestring):
			val = int(val)
		self._defaultSpacing = val


	def _getForm(self):
		parent = self.Parent
		if isinstance(parent, dabo.ui.dFormMixin):
			return parent
		elif isinstance(parent, dabo.ui.dPemMixin):
			return parent.Form
		return None


	def _getHeight(self):
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
				# The sizer is not nested; it is "unattached"
				return None
			else:
				ob = cs
				ret = ob._parent
		return ret

	def _setParent(self, obj):
		self._parent = obj


	def _getVisible(self):
		try:
			return self._visible
		except AttributeError:
			default = True
			self._setVisible(default)
			return default

	def _setVisible(self, val):
		if isinstance(val, basestring):
			val = (val.lower()[0] in ("t", "y"))
		self._visible = val
		self.ShowItems(val)


	def _getWidth(self):
		return self.GetSize()[0]


	Children = property(_getChildren, None, None,
			_("List of all the sizer items managed by this sizer  (list of sizerItems"))

	ChildObjects = property(_getChildObjects, None, None,
			_("""List of all the objects (controls, sizers, spacers) that are directly managed
			by this sizer  (list of objects"""))

	ChildSizers = property(_getChildSizers, None, None,
			_("List of all the sizers that are directly managed by this sizer  (list of sizers"))

	ChildSpacers = property(_getChildSpacers, None, None,
			_("List of all the spacer items that are directly managed by this sizer  (list of spacer items"))

	ChildWindows = property(_getChildWindows, None, None,
			_("List of all the windows that are directly managed by this sizer  (list of controls"))

	ControllingSizer = property(_getCntrlSizer, None, None,
			_("""Reference to the sizer that controls this control's layout.  (dSizer)"""))

	ControllingSizerItem = property(_getCntrlSzItem, None, None,
			_("""Reference to the sizer item that control's this control's layout.
				This is useful for getting information about how the item is being
				sized, and for changing those settings."""))

	DefaultBorder = property(_getDefaultBorder, _setDefaultBorder, None,
			_("""Sets a default value for the border that will be applied to any controls added
			to the sizer afterwards for whom an explicit value for the border is not set.
			Note that it does not affect the border of items already added to the control.
			This property is useful when you want to add a series of items to a sizer with
			the same border: just set this property once, and then add your items.
			Default=0  (int)"""))

	DefaultBorderAll = property(_getDefaultBorderAll, _setDefaultBorderAll, None,
			_("""When True, the DefaultBorder property is applied to all of the sides of
			any controls added to the sizer. If any of the individual side properties,
			such as DefaultBorderTop, are set to False, this property will return False.
			Setting DefaultBorderAll will effectively set all of the individual side properties
			to that value. Default=True  (bool)"""))

	DefaultBorderBottom = property(_getDefaultBorderBottom,
			_setDefaultBorderBottom, None,
			_("""Affects whether the DefaultBorder property is applied to the Bottom
			side of controls added to the sizer. Default=True  (bool)"""))

	DefaultBorderLeft = property(_getDefaultBorderLeft,
			_setDefaultBorderLeft, None,
			_("""Affects whether the DefaultBorder property is applied to the Left
			side of controls added to the sizer. Default=True  (bool)"""))

	DefaultBorderRight = property(_getDefaultBorderRight,
			_setDefaultBorderRight, None,
			_("""Affects whether the DefaultBorder property is applied to the Right
			side of controls added to the sizer. Default=True  (bool)"""))

	DefaultBorderTop = property(_getDefaultBorderTop,
			_setDefaultBorderTop, None,
			_("""Affects whether the DefaultBorder property is applied to the Top
			side of controls added to the sizer. Default=True  (bool)"""))

	DefaultSpacing = property(_getDefaultSpacing, _setDefaultSpacing, None,
			_("Amount of space automatically inserted between elements.  (int)"))

	Form = property(_getForm, None, None,
			_("Form with which the sizer is associated.  (dForm or None)"))

	Height = property(_getHeight, None, None,
			_("Height of the sizer  (int)"))

	Orientation = property(_getOrientation, _setOrientation, None,
			_("Sets the orientation of the sizer, either 'Vertical' or 'Horizontal'."))

	Parent = property(_getParent, _setParent, None,
			_("""The object that contains this sizer. In the case of nested
			sizers, it is the object that the outermost sizer belongs to. (obj)"""))

	Visible = property(_getVisible, _setVisible, None,
			_("Specifies whether the sizer and contained items are shown  (bool)"))

	Width = property(_getWidth, None, None,
			_("Width of this sizer  (int)"))


	DynamicDefaultBorder = makeDynamicProperty(DefaultBorder)
	DynamicVisible = makeDynamicProperty(Visible)
