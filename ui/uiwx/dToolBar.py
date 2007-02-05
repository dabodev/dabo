import os.path
import warnings
import wx
import dabo, dabo.ui

dabo.ui.loadUI("wx")

import dControlMixin as cm
import dMenu
from dabo.dLocalize import _
import dabo.dEvents as dEvents
from dabo.dObject import dObject
from dabo.ui import makeDynamicProperty


class dToolBar(cm.dControlMixin, wx.ToolBar):
	"""Creates a toolbar, which is a menu-like collection of icons.

	You may also add items to a toolbar such as separators and real Dabo
	controls, such as dropdown lists, radio boxes, and text boxes.

	The toolbar can be detached into a floating toolbar, and reattached by the
	user at will.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dToolBar
		preClass = wx.PreToolBar
		
		style = self._extractKey((kwargs, properties, attProperties), "style", 0)
		# Note: need to set the TB_TEXT flag, in order for that to be toggleable
		#       after instantiation. Because most toolbars will want to have icons
		#       only, there is code in _initProperties to turn it off by default.
		kwargs["style"] = style | wx.TB_TEXT

		# wx doesn't return anything for GetChildren(), but we are giving Dabo
		# that feature, for easy polymorphic referencing of the buttons and 
		# controls in a toolbar.
		self._daboChildren = []

		# Need this to load/convert image files to bitmaps
		self._image = wx.NullImage

		cm.dControlMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)


	def _initProperties(self):
		# default to no text captions (this fires before user subclass code and user
		# overriding arguments, so it won't conflict if the user sets ShowCaptions		
		# explicitly.
		self.ShowCaptions = False
		self.Dockable = True
		super(dToolBar, self)._initProperties()


	def _getInitPropertiesList(self):
		additional = ["Dockable",]
		original = list(super(dToolBar, self)._getInitPropertiesList())
		return tuple(original + additional)


	def _realize(self):
		"""There seems to be a bug in wxPython Mac since 2.8. There is an error
		thrown, but it doesn't seem to affect the behavior of the toolbar, so just
		let it pass.
		"""
		try:
			self.Realize()
		except wx._core.PyAssertionError, e:
			# Only happens on the Mac
			pass


	def appendItem(self, item):
		"""Insert a dToolBarItem at the end of the toolbar."""
		wxItem = self.AddToolItem(item._wxToolBarItem)
		self._daboChildren.append(item)
		item._parent = self
		self._realize()
		return item


	def insertItem(self, pos, item):
		"""Insert a dToolBarItem before the specified position in the toolbar."""
		wxItem = self.InsertToolItem(pos, item._wxToolBarItem)
		self._daboChildren.insert(pos, item)
		item._parent = self
		self._realize()
		return item
		

	def prependItem(self, item):
		"""Insert a dToolBarItem at the beginning of the toolbar."""
		self.insertItem(0, item)
		return item


	def appendButton(self, caption, pic, bindfunc=None, toggle=False, 
			tip="", help="", *args, **kwargs):
		"""Adds a tool (button) to the toolbar. 

		You must pass a caption and an image for the button. The picture can be a 
		wx.Bitmap, or a path to an image file of any supported type. If you pass 
		toggle=True, the button will exist in an up and down state. Pass the 
		function you want to be called when this button is clicked in an 
		'OnHit' param.

		NOTE: use of the bindfunc parameter is deprecated in version 0.8 and will be
		removed	in version 0.9. Send an OnHit parameter instead.
		"""
		return self._appendInsertButton(None, caption, pic, bindfunc, 
				toggle,	tip, help, *args, **kwargs)


	def insertButton(self, pos, caption, pic, bindfunc=None, toggle=False, 
			tip="", help="", *args, **kwargs):
		"""Inserts a tool (button) to the toolbar at the specified position. 

		You must pass a caption and an image for the button. The picture can be a 
		wx.Bitmap, or a path to an image file of any supported type. If you pass 
		toggle=True, the button will exist in an up and down state. Pass the 
		function you want to be called when this button is clicked in an 
		'OnHit' param.

		NOTE: use of the bindfunc parameter is deprecated in version 0.8 and will be
		removed	in version 0.9. Send an OnHit parameter instead.
		"""
		return self._appendInsertButton(pos, caption, pic, bindfunc, 
				toggle,	tip, help, *args, **kwargs)


	def prependButton(self, caption, pic, bindfunc=None, toggle=False, 
			tip="", help="", *args, **kwargs):
		"""Inserts a tool (button) to the beginning of the toolbar. 

		You must pass a caption and an image for the button. The picture can be a 
		wx.Bitmap, or a path to an image file of any supported type. If you pass 
		toggle=True, the button will exist in an up and down state. Pass the 
		function you want to be called when this button is clicked in an 
		'OnHit' param.

		NOTE: use of the bindfunc parameter is deprecated in version 0.8 and will be
		removed	in version 0.9. Send an OnHit parameter instead.
		"""
		return self.insertButton(0, caption, pic, bindfunc, toggle,	tip, help, *args, **kwargs)


	def _appendInsertButton(self, pos, caption, pic, bindfunc, toggle, 
			tip, help, *args, **kwargs):
		"""Common code for the append|insert|prependButton() functions."""
		if isinstance(pic, basestring):
			# path was passed
			picBmp = dabo.ui.strToBmp(pic)
		else:
			picBmp = pic
		
		wd, ht = picBmp.GetWidth(), picBmp.GetHeight()
		needScale = False
		
		if (self.MaxWidth > 0) and (wd > self.MaxWidth):
			wd = self.MaxWidth
			needScale = True
		if (self.MaxHeight > 0) and (ht > self.MaxHeight):
			ht = self.MaxHeight
			needScale = True
		if needScale:
			picBmp = self._resizeBmp(picBmp, wd, ht)

		if toggle:
			kind = wx.ITEM_CHECK
		else:
			kind = wx.ITEM_NORMAL
		id_ = wx.NewId()
		if pos is None:
			# append
			tool = self.DoAddTool(id_, caption, picBmp, shortHelp=tip, longHelp=help,
					kind=kind)
		else:
			# insert
			tool = self.InsertTool(pos, id_, caption, picBmp, shortHelpString=tip, longHelpString=help,
					isToggle=toggle)
		butt = dToolBarItem(tool, *args, **kwargs)
		
		try:
			self.SetToggle(id_, toggle)
		except wx._core.PyAssertionError:
			## The AssertionError: not implemented occurs on wxMac, even though
			## SetToggle() obviously is implemented, because it does work.
			pass

		if bindfunc is not None:
			warnings.warn(_("Deprecated; use 'OnHit=<func>' instead."), 
					DeprecationWarning, 1)
			butt.bindEvent(dEvents.Hit, bindfunc)
		self._realize()
		
		# Store the button reference
		if pos is None:
			self._daboChildren.append(butt)
		else:
			self._daboChildren.insert(pos, butt)
		butt._parent = self

		return butt
			

	def appendControl(self, control, bindfunc=None):
		"""Adds any Dabo Control to the toolbar. 

		Optionally, pass the function you want to be called when this button is 
		clicked in the bindfunc parameter.
		"""
		butt = self.AddControl(control)
		butt.SetLabel(control.Caption)
		if bindfunc:
			control.bindEvent(dEvents.Hit, bindfunc)
		self._realize()
		
		# Store the control reference:
		self._daboChildren.append(control)

		return control


	def insertControl(self, pos, control, bindfunc=None):
		"""Inserts any Dabo Control to the toolbar at the specified position. 

		Optionally, pass the function you want to be called when this button is 
		clicked in the bindfunc parameter.
		"""
		butt = self.InsertControl(pos, control)
		butt.SetLabel(control.Caption)
		if bindfunc:
			control.bindEvent(dEvents.Hit, bindfunc)
		self._realize()
		
		# Store the control reference:
		self._daboChildren.insert(0, control)

		return control


	def prependControl(self, control, bindfunc=None):
		"""Inserts any Dabo Control to the beginning of the toolbar. 

		Optionally, pass the function you want to be called when this button is 
		clicked in the bindfunc parameter.
		"""
		return self.insertControl(0, control, bindfunc)


	def appendSeparator(self):
		"""Inserts a separator at the end of the toolbar."""
		sep = dToolBarItem(self.AddSeparator())
		self._daboChildren.append(sep)
		sep._parent = self
		self._realize()
		return sep
		

	def insertSeparator(self, pos):
		"""Inserts a separator before the specified position in the toolbar."""
		sep = dToolBarItem(self.InsertSeparator(pos))
		self._daboChildren.insert(pos, sep)
		sep._parent = self
		self._realize()
		return sep


	def prependSeparator(self):
		"""Inserts a separator at the beginning of the toolbar."""
		return self.insertSeparator(0)
	
	
	def remove(self, index, release=True):
		"""Removes the item at the specified index from the toolbar.

		If release is True (the default), the item is deleted as well. If release 
		is False, a reference to the  object will be returned, and the caller 
		is responsible for deleting it.
		"""
		item = self.Children[index]
		id_ = item._id
		del(self._daboChildren[index])
		self.RemoveTool(id_)
		item._parent = None
		if release:
			item.Destroy()
		return item


	def getItemIndex(self, caption):
		"""Returns the index of the item with the specified caption.

		If the item isn't found, None is returned.
		"""
		for pos, itm in enumerate(self.Children):
			if itm.Caption == caption:
				return pos
		return None
		

	def getItem(self, caption):
		"""Returns a reference to the item with the specified caption.

		If the item isn't found, None is returned.
		"""
		idx = self.getItemIndex(caption)
		if idx is not None:
			return self.Children[idx]
		return None


	def _resizeBmp(self, bmp, wd, ht):
		img = bmp.ConvertToImage()
		img.Rescale(wd, ht)
		return img.ConvertToBitmap()


	def _updBmpSize(self):
		toolBmpWd, toolBmpHt = self.GetToolBitmapSize()
		if self.MaxWidth:
			toolBmpWd = self.MaxWidth
		if self.MaxHeight:
			toolBmpHt = self.MaxHeight
		self.SetToolBitmapSize((toolBmpWd, toolBmpHt))


	def GetChildren(self):
		## This overrides the wx default which just returns an empty list.
		return self._daboChildren

	
	def _recreateItem(self, item):
		"""Recreate the passed dToolBarItem, and put it back in its original place.

		This is necessary when changing some or all of the dToolBarItem properties,
		and is called from within that object as a callafter.
		"""
		id_ = item._id
		idx = self._getIndexByItem(item)
		if idx is not None:
			self.remove(idx, False)
			self.insertItem(idx, item)		


	def _getIndexByItem(self, item):
		"""Given a dToolBarItem object reference, return the index in the toolbar.

		Return None if the item doesn't exist in the toolbar.
		"""
		for idx, o in enumerate(self.Children):
			if o == item:
				return idx
		return None


	def _getDockable(self):
		return self._hasWindowStyleFlag(wx.TB_DOCKABLE)

	def _setDockable(self, val):
		self._delWindowStyleFlag(wx.TB_DOCKABLE)
		if val:
			self._addWindowStyleFlag(wx.TB_DOCKABLE)
		
		
	def _getForm(self):
		try:
			v = self._form
		except AttributeError:
			v = self._form = None
		return v

	def _setForm(self, val):
		self._form = val	

	
	def _getMaxHt(self):
		try:
			v = self._maxHt
		except AttributeError:
			v = self._maxHt = 0
		return v

	def _setMaxHt(self, val):
		self._maxHt = val
		if self._constructed():
			self._updBmpSize()
		else:
			self._properties["MaxHeight"] = val
		
		
	def _getMaxWd(self):
		try:
			v = self._maxWd
		except AttributeError:
			v = self._maxWd = 0
		return v

	def _setMaxWd(self, val):
		self._maxWd = val
		if self._constructed():
			self._updBmpSize()
		else:
			self._properties["MaxWidth"] = val
		
		
	def _getShowCaptions(self):
		return self._hasWindowStyleFlag(wx.TB_TEXT)

	def _setShowCaptions(self, val):
		if self._constructed():
			self._delWindowStyleFlag(wx.TB_TEXT)
			if val:
				self._addWindowStyleFlag(wx.TB_TEXT)
			self._realize()
		else:
			self._properties["ShowCaptions"] = val
		
		
	def _getShowIcons(self):
		return not self._hasWindowStyleFlag(wx.TB_NOICONS)

	def _setShowIcons(self, val):
		if self._constructed():
			self._delWindowStyleFlag(wx.TB_NOICONS)
			if not val:
				self._addWindowStyleFlag(wx.TB_NOICONS)
			self._realize()
		else:
			self._properties["ShowIcons"] = val
		
		
	Dockable = property(_getDockable, _setDockable, None,
		_("""Specifies whether the toolbar can be docked and undocked.  (bool)

			Currently, this only seems to work on Linux, and can't be changed after
			instantiation. Default is True."""))

	Form = property(_getForm, _setForm, None,
		_("Specifies the form that we are a member of."))
	
	MaxHeight = property(_getMaxHt, _setMaxHt, None,
		_("""Specifies the maximum height of added buttons.  (int)

		When set to zero, there will be no height limit.""" ) )

	MaxWidth = property(_getMaxWd, _setMaxWd, None,
		_("""Specifies the maximum width of added buttons.  (int)

		When set to zero, there will be no width limit.""" ) )

	ShowCaptions = property(_getShowCaptions, _setShowCaptions, None,
		_("""Specifies whether the text captions are shown in the toolbar.  (bool)

		Default is False."""))

	ShowIcons = property(_getShowIcons, _setShowIcons, None,
		_("""Specifies whether the icons are shown in the toolbar.  (bool)

		Note that you can set both ShowCaptions and ShowIcons to False, but in 
		that case, the icons will still show. Default is True."""))


	DynamicShowCaptions = makeDynamicProperty(ShowCaptions)
	DynamicShowIcons = makeDynamicProperty(ShowIcons)



class dToolBarItem(dObject):
	"""Creates a toolbar item."""
	## I can't figure out, for the life of me, how to mix-in dObject with 
	## wx.ToolBarToolBase - I always get a RunTimeError that there isn't a
	## constructor. Therefore, I've made this wrapper class to decorate the
	## wx.ToolBarToolBase instance that comes back from the DoAddTool()
	## function.
	def __init__(self, wxItem=None, OnHit=None, *args, **kwargs):
		if wxItem is None:
			wxItem = self._getWxToolBarItem()
		self._wxToolBarItem = wxItem
		self._id = wxItem.GetId()
		self._parent = None
		if self.Application:
			self.Application.uiApp.Bind(wx.EVT_MENU, self.__onWxHit, wxItem)
		super(dToolBarItem, self).__init__(*args, **kwargs)
		if OnHit is not None:
			self.bindEvent(dEvents.Hit, OnHit)
			

	def __getattr__(self, attr):
		"""Exposes the underlying wx functions and attributes."""
		if hasattr(self._wxToolBarItem, attr):
			return getattr(self._wxToolBarItem, attr)
		raise AttributeError


	def _getWxToolBarItem(self):
		"""Create the underlying wxToolBarToolBase item, and attach it to self."""
		# The only way I can figure out how to do this is to call 
		# toolbar.DoAddTool() and save the result. Hence, the throwaway toolbar.
		tb = dToolBar(self.Application.ActiveForm)
		id_ = wx.NewId()
		wxItem = tb.DoAddTool(id_, "temp", dabo.ui.strToBmp("dCheckBox"))
		tb.RemoveTool(id_)
		tb.release()
		return wxItem


	def __onWxHit(self, evt):
		self.raiseEvent(dEvents.Hit)


	def _getCanToggle(self):
		return bool(self._wxToolBarItem.CanBeToggled())

	def _setCanToggle(self, val):
		self._wxToolBarItem.SetToggle(bool(val))


	def _getCaption(self):
		return self._wxToolBarItem.GetLabel()

	def _setCaption(self, val):
		self._wxToolBarItem.SetLabel(val)
		if self.Parent:
			dabo.ui.callAfter(self.Parent._recreateItem, self)


	def _getEnabled(self):
		return self.Parent.GetToolEnabled(self._id)

	def _setEnabled(self, val):
		if self.Parent:
			self.Parent.EnableTool(self._id, bool(val))
		else:
			self.Enable(bool(val))


	def _getParent(self):
		## Calling GetToolBar() on a free item causes a segfault.
		#return self._wxToolBarItem.GetToolBar()
		return self._parent


	def _getValue(self):
		if self.CanToggle:
			return bool(self.Parent.GetToolState(self._id))
		return None

	def _setValue(self, val):
		assert self.CanToggle, "Can't set Value on a non-toggleable tool."
		if self.Parent:
			self.Parent.ToggleTool(self._id, bool(val))
		else:
			if bool(self.IsToggled()) != bool(val):
				self.Toggle()


	CanToggle = property(_getCanToggle, _setCanToggle, None,
			_("""Specifies whether the toolbar item can be toggled.  (bool)

			For toggleable items, the Value property will tell you if the item is
			currently toggled or not."""))

	Caption = property(_getCaption, _setCaption, None,
			_("""Specifies the text caption of the toolbar item.

			You will only see the caption if dToolBar.ShowCaptions is set to True.
			"""))

	Enabled = property(_getEnabled, _setEnabled, None,
			_("""Specifies whether the user may interact with the button."""))

	Parent = property(_getParent, None, None,
			_("""Contains an object reference to the containing toolbar."""))

	Value = property(_getValue, _setValue, None,
			_("""Specifies whether the toolbar item is toggled or not.  (bool)

			For items with CanToggle = True, returns one of True or False, depending
			on the state of the button. For items with CanToggle = False, returns
			None."""))


	DynamicCaption = makeDynamicProperty(Caption)
	DynamicEnabled = makeDynamicProperty(Enabled)



class _dToolBar_test(dToolBar):
	def initProperties(self):
		self.MaxWidth = 20
		self.MaxHeight = 20

	def afterInit(self):
		self.appendButton("Copy", pic="copy", toggle=False, OnHit=self.onCopy, 
				tip="Copy", help="Much Longer Copy Help Text")

		self.appendButton("Timer", pic="dTimer", toggle=True, OnHit=self.onTimer,
				tip="Timer Toggle", help="Timer Help Text")

		self.appendButton("Dabo", pic="daboIcon128", toggle=True, tip="Dabo! Dabo! Dabo!", 
				help="Large icon resized to fit in the max dimensions")

		self.appendSeparator()

		self.appendButton("Exit", pic="close", toggle=True, OnHit=self.onExit, 
				tip="Exit", help="Quit the application")

	def onCopy(self, evt):
		dabo.ui.info("Copy Clicked!")

	def onTimer(self, evt):
		item = evt.EventObject
		dabo.ui.info("CHECKED: %s, ID: %s" % (item.Value, item.GetId()))

	def onExit(self, evt):
		app = self.Application
		if app:
			app.onFileExit(None)
		else:
			dabo.ui.stop("Sorry, there isn't an app object - can't exit.")

if __name__ == "__main__":
	import test
	test.Test().runTest(_dToolBar_test)
