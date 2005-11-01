""" dToolBar.py """
import wx
import dabo, dabo.ui
import os.path

dabo.ui.loadUI("wx")

import dControlMixin as cm
import dMenu
from dabo.dLocalize import _
import dabo.dEvents as dEvents


class dToolBar(wx.ToolBar, cm.dControlMixin):
	"""Creates a toolbar, which can contain buttons that behave
	more like menu items than regular controls. Other controls,
	such as dropdown lists, can also be added.
	"""
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dToolBar
		preClass = wx.PreToolBar
		
		style = self._extractKey(kwargs, "style", 0)
		kwargs["style"] = style |  wx.TB_DOCKABLE | wx.TB_TEXT

		# wx doesn't return anything for GetChildren(), but we are giving Dabo
		# that feature, for easy polymorphic referencing of the buttons and 
		# controls in a toolbar.
		self._daboChildren = []

		# Need this to load/convert image files to bitmaps
		self._image = wx.NullImage

		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
		

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
		
		butt = self.AddSimpleTool(id_, bitmap=picBmp, isToggle=toggle, 
				shortHelpString=tip, longHelpString=help)
		butt.SetLabel(caption)
		if bindfunc and self.Application:
			self.Application.uiApp.Bind(wx.EVT_MENU, bindfunc, butt)
		self.Realize()
		
		# Store the button reference
		self._daboChildren.append(butt)
		
			
	def appendControl(self, control, bindfunc=None):
		"""Adds any Dabo Control to the toolbar. 

		Pass the function you want to be called when this button is clicked in the 
		'bindfunc' param.
		"""
		butt = self.AddControl(control)
		butt.SetLabel(control.Caption)
		if bindfunc and self.Application:
			control.bindEvent(dEvents.Hit, bindfunc)
		self.Realize()
		
		# Store the button reference
		self._daboChildren.append(butt)

		return control


	def appendSeparator(self):
		sep = self.AddSeparator()
		self._daboChildren.append(sep)
		self.Realize()
		
		
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
		
		
	Form = property(_getForm, _setForm, None,
		_("Specifies the form that we are a member of."))
	
	MaxHeight = property(_getMaxHt, _setMaxHt, None,
		_("""When set to a value greater than zero, will limit the height of 
		added buttons to this value. (int)""" ) )

	MaxWidth = property(_getMaxWd, _setMaxWd, None,
		_("""When set to a value greater than zero, will limit the width of 
		added buttons to this value. (int)""" ) )


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
		dabo.ui.info("CHECKED: %s, ID: %s" % (evt.Checked(), evt.GetId()))

	def onExit(self, evt):
		app = self.Application
		if app:
			app.onFileExit(None)
		else:
			dabo.ui.stop("Sorry, there isn't an app object - can't exit.")

if __name__ == "__main__":
	import test
	test.Test().runTest(_dToolBar_test)
