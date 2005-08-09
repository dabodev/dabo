""" dToolBar.py """
import wx
import dabo
import os.path
from dPemMixin import dPemMixin as pm
import dMenu
from dabo.dLocalize import _
import dabo.dEvents as dEvents

dabo.ui.loadUI("wx")

class dToolBar(wx.ToolBar, pm):
	"""Creates a toolbar, which can contain buttons that behave
	more like menu items than regular controls. Other controls,
	such as dropdown lists, can also be added.
	"""
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dToolBar
		preClass = wx.PreToolBar
		
		# Get the max props, if any
		maxwd = self.extractKey(kwargs, "MaxWidth", 0)
		maxht = self.extractKey(kwargs, "MaxHeight", 0)
		style = self.extractKey(kwargs, "style", 0)
		kwargs["style"] = style |  wx.TB_DOCKABLE | wx.TB_TEXT
		
		pm.__init__(self, preClass, parent, properties, *args, **kwargs)
		
		# We need to track tool IDs internally for referencing the 
		# buttons once they are created
		self._nextToolID = 0
		self._tools = {}
		# Need this to load/convert image files to bitmaps
		self._image = wx.NullImage
		# Limits the size of buttons. Zero implies no limit.
		self._maxWd = maxwd
		self._maxHt = maxht
		# Update the props. This will also update the tool's bitmap size
		self.MaxWidth = maxwd
		self.MaxHeight = maxht
		

	def appendButton(self, name, pic, bindfunc=None, toggle=False, tip="", help=""):
		"""Adds a tool (button) to the toolbar. You must pass an image for the 
		button; it can be a wx.Bitmap, or a path to an image file. If you pass
		toggle=True, the button will exist in an up and down state. Pass the function 
		you want to be called when this button is clicked in the 'bindfunc' param.
		"""
		id = self._NextToolID
		if isinstance(pic, basestring):
			# path was passed
			picBmp = self.strToBmp(pic)
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
		
		butt = self.AddSimpleTool(id, bitmap=picBmp, isToggle=toggle, 
				shortHelpString=tip, longHelpString=help)
		butt.SetLabel(name)
		if bindfunc:
			self.Application.uiApp.Bind(wx.EVT_MENU, bindfunc, butt)
		self.Realize()
		
		# Store the button reference
		self._tools[name] = butt
		
			
	def appendSeparator(self):
		self.AddSeparator()
		self.Realize()
		
		
	def strToBmp(self, val):
		"""This can be either a path, or the name of a built-in graphic."""
		ret = None
		if os.path.exists(val):
			ret = self.pathToBmp(val)
		else:
			# See if it's a standard icon
			ret = dabo.ui.dIcons.getIconBitmap(val)
			if not ret:
				# See if it's a built-in graphic
				ret = dabo.ui.getBitmap(val)
		return ret
		
		
	def pathToBmp(self, pth):
		img = self._image
		img.LoadFile(pth)
		return img.ConvertToBitmap()


	def resizeBmp(self, bmp, wd, ht):
		img = bmp.ConvertToImage()
		img.Rescale(wd, ht)
		return img.ConvertToBitmap()


	def updBmpSize(self):
		toolBmpWd, toolBmpHt = self.GetToolBitmapSize()
		if self._maxWd:
			toolBmpWd = self._maxWd
		if self._maxHt:
			toolBmpHt = self._maxHt
		self.SetToolBitmapSize((toolBmpWd, toolBmpHt))



#- 	def GetChildren(self):
#- 		# wx doesn't provide GetChildren() for menubars or menus, but dPemMixin
#- 		# calls it in _getChildren(). The Dabo developer wants the submenus of
#- 		# the menubar, but is using the consistent Children property to do it.
#- 		children = [self.GetMenu(index) for index in range(self.GetMenuCount())]
#- 		return children

	def _getForm(self):
		return self.GetFrame()

	def _setForm(self, val):
		if self._constructed():
			if val != self.GetFrame():
				self.Detach()
				self.Attach(val)
		else:
			self._properties["Form"] = val
	
	
	def _getMaxHt(self):
		return self._maxHt
	def _setMaxHt(self, val):
		self._maxHt = val
		self.updBmpSize()
		
		
	def _getMaxWd(self):
		return self._maxWd
	def _setMaxWd(self, val):
		self._maxWd = val
		self.updBmpSize()
		
		
	def _getNextID(self):
		ret = self._nextToolID
		self._nextToolID += 1
		return ret
		

	Form = property(_getForm, _setForm, None,
		_("Specifies the form that we are a member of."))
	
	MaxHeight = property(_getMaxHt, _setMaxHt, None,
		_("""When set to a value greater than zero, will limit the height of 
		added buttons to this value. (int)""" ) )

	MaxWidth = property(_getMaxWd, _setMaxWd, None,
		_("""When set to a value greater than zero, will limit the width of 
		added buttons to this value. (int)""" ) )

	_NextToolID = property(_getNextID, None, None, 
		_("Next Available ID for tracking toolbar buttons  (int)"))

		

if __name__ == "__main__":
	def clickCopy(evt):
		dabo.ui.info("Copy Clicked!")
	def clickTimer(evt):
		dabo.ui.info("CHECKED: %s, ID: %s" % (evt.Checked(), evt.GetId()))
	app = dabo.dApp()
	app.setup()
	mf = app.MainForm
	mf.ShowToolBar = True
	tb = mf.ToolBar
	tb.MaxWidth=20
	tb.MaxHeight=20
	tb.appendButton("Copy", pic="copy", toggle=False, bindfunc=clickCopy, 
			tip="Copy", help="Much Longer Copy Help Text")
	tb.appendButton("Timer", pic="dTimer", toggle=True, bindfunc=clickTimer,
			tip="Timer Toggle", help="Timer Help Text")
	tb.appendButton("Dabo", pic="daboIcon128", toggle=True, tip="Dabo! Dabo! Dabo!", 
			help="Large icon resized to fit in the max dimensions")
	tb.appendSeparator()
	tb.appendButton("Exit", pic="close", toggle=True, bindfunc=app.onFileExit, 
			tip="Exit", help="Quit the application")
	
 	app.start()
	
