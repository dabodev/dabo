""" dToolBar.py """
import wx
import dabo, dabo.ui
import os.path

dabo.ui.loadUI("wx")

import dControlMixin as cm
import dMenu
from dabo.dLocalize import _
import dabo.dEvents as dEvents
from dabo.dObject import dObject


class dToolBar(wx.ToolBar, cm.dControlMixin):
	"""Creates a toolbar, which is a menu-like collection of icons.

	You may also add items to a toolbar such as separators and real Dabo
	controls, such as dropdown lists, radio boxes, and text boxes.

	The toolbar can be detached into a floating toolbar, and reattached by the
	user at will.
	"""
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dToolBar
		preClass = wx.PreToolBar
		
		style = self._extractKey(kwargs, "style", 0)
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

		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)


	def _initProperties(self):
		# default to no text captions (this fires before user subclass code and user
		# overriding arguments, so it won't conflict if the user sets ShowCaptions		
		# explicitly.
		self.ShowCaptions = False
		self.Dockable = True
		super(dToolBar, self)._initProperties()


	def _getInitPropertiesList(self):
		additional = ["Dockable", ]
		original = list(super(dToolBar, self)._getInitPropertiesList())
		return tuple(original + additional)


	def appendButton(self, caption, pic, bindfunc=None, toggle=False, 
			tip="", help=""):
		"""Adds a tool (button) to the toolbar. 

		You must pass a caption and an image for the button. The picture can be a 
		wx.Bitmap, or a path to an image file of any supported type. If you pass 
		toggle=True, the button will exist in an up and down state. Pass the 
		function you want to be called when this button is clicked in the 
		'bindfunc' param.
		"""
		id_ = wx.NewId()
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
			picBmp = self.resizeBmp(picBmp, wd, ht)
	
		butt = dToolBarItem(self.DoAddTool(id_, caption, picBmp, 
				shortHelp=tip, longHelp=help))

		if toggle:
			self.SetToggle(id_, True)

		if bindfunc:
			butt.bindEvent(dEvents.Hit, bindfunc)
		self.Realize()
		
		# Store the button reference
		self._daboChildren.append(butt)
		
		return butt
			

	def appendControl(self, control, bindfunc=None):
		"""Adds any Dabo Control to the toolbar. 

		Pass the function you want to be called when this button is clicked in the 
		'bindfunc' param.
		"""
		butt = self.AddControl(control)
		butt.SetLabel(control.Caption)
		if bindfunc:
			control.bindEvent(dEvents.Hit, bindfunc)
		self.Realize()
		
		# Store the control reference:
		self._daboChildren.append(control)

		return control


	def appendSeparator(self):
		sep = dToolBarItem(self.AddSeparator())
		self._daboChildren.append(sep)
		self.Realize()
		return sep
		
		
	def resizeBmp(self, bmp, wd, ht):
		img = bmp.ConvertToImage()
		img.Rescale(wd, ht)
		return img.ConvertToBitmap()


	def updBmpSize(self):
		toolBmpWd, toolBmpHt = self.GetToolBitmapSize()
		if self.MaxWidth:
			toolBmpWd = self.MaxWidth
		if self.MaxHeight:
			toolBmpHt = self.MaxHeight
		self.SetToolBitmapSize((toolBmpWd, toolBmpHt))


	def GetChildren(self):
		## This overrides the wx default which just returns an empty list.
		return self._daboChildren


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
			self.updBmpSize()
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
			self.updBmpSize()
		else:
			self._properties["MaxWidth"] = val
		
		
	def _getShowCaptions(self):
		return self._hasWindowStyleFlag(wx.TB_TEXT)

	def _setShowCaptions(self, val):
		if self._constructed():
			self._delWindowStyleFlag(wx.TB_TEXT)
			if val:
				self._addWindowStyleFlag(wx.TB_TEXT)
			self.Realize()
		else:
			self._properties["ShowCaptions"] = val
		
		
	def _getShowIcons(self):
		return not self._hasWindowStyleFlag(wx.TB_NOICONS)

	def _setShowIcons(self, val):
		if self._constructed():
			self._delWindowStyleFlag(wx.TB_NOICONS)
			if not val:
				self._addWindowStyleFlag(wx.TB_NOICONS)
			self.Realize()
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
		that case, the icons will still show.

		Default is True."""))


class dToolBarItem(dObject):
	"""Creates a toolbar item."""
	## I can't figure out, for the life of me, how to mix-in dObject with 
	## wx.ToolBarToolBase - I always get a RunTimeError that there isn't a
	## constructor. Therefore, I've made this wrapper class to decorate the
	## wx.ToolBarToolBase instance that comes back from the DoAddTool()
	## function.
	def __init__(self, wxToolBarToolBase):
		self._wxToolBarItem = wxToolBarToolBase
		if self.Application:
			self.Application.uiApp.Bind(wx.EVT_MENU, self.__onWxHit, 
					wxToolBarToolBase)

	def __getattr__(self, attr):
		if hasattr(self._wxToolBarItem, attr):
			return getattr(self._wxToolBarItem, attr)
		raise AttributeError

	def __onWxHit(self, evt):
		self.raiseEvent(dEvents.Hit)


class _dToolBar_test(dToolBar):
	def initProperties(self):
		self.MaxWidth = 20
		self.MaxHeight = 20

	def afterInit(self):
		self.appendButton("Copy", pic="copy", toggle=False, bindfunc=self.onCopy, 
				tip="Copy", help="Much Longer Copy Help Text")

		self.appendButton("Timer", pic="dTimer", toggle=True, bindfunc=self.onTimer,
				tip="Timer Toggle", help="Timer Help Text")

		self.appendButton("Dabo", pic="daboIcon128", toggle=True, tip="Dabo! Dabo! Dabo!", 
				help="Large icon resized to fit in the max dimensions")

		self.appendSeparator()

		self.appendButton("Exit", pic="close", toggle=True, bindfunc=self.onExit, 
				tip="Exit", help="Quit the application")

	def onCopy(self, evt):
		dabo.ui.info("Copy Clicked!")

	def onTimer(self, evt):
		item = evt.EventObject
		dabo.ui.info("CHECKED: %s, ID: %s" % (item.IsToggled(), item.GetId()))

	def onExit(self, evt):
		app = self.Application
		if app:
			app.onFileExit(None)
		else:
			dabo.ui.stop("Sorry, there isn't an app object - can't exit.")

if __name__ == "__main__":
	import test
	test.Test().runTest(_dToolBar_test)
