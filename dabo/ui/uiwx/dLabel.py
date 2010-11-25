# -*- coding: utf-8 -*-
import wx
import dabo
import dabo.dEvents as dEvents
from dabo.dLocalize import _

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
from dabo.ui import makeDynamicProperty
from alignmentMixin import AlignmentMixin


class dLabel(cm.dControlMixin, AlignmentMixin, wx.StaticText):
	"""Creates a static label, to make a caption for another control, for example."""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dLabel
		self._wordWrap = False
		self._inResizeEvent = False
		preClass = wx.PreStaticText
		cm.dControlMixin.__init__(self, preClass, parent, properties, attProperties,
				*args, **kwargs)
		self.bindEvent(dEvents.Resize, self.__onResize)


	def __onResize(self, evt):
		"""Event binding is set when WordWrap=True. Tell the label
		to wrap to its current width.
		"""
		if self._inResizeEvent:
			return
		self._inResizeEvent = True
		dabo.ui.callAfter(self.__onResizeExecute)

	def __onResizeExecute(self):
		# We need to set the caption to the internally-saved caption, since
		# WordWrap can introduce additional linefeeds.
		try:
			self.Parent.lockDisplay()
			pass
		except dabo.ui.deadObjectException:
			# Form is being destroyed; bail
			return
		plat = self.Application.Platform
		try:
			first = self._firstResizeEvent
		except AttributeError:
			first = True
			self._firstResizeEvent = False
#		if plat == "Win":
#			self.InvalidateBestSize()
#			self.Parent.layout()
#		self.Parent.layout()
		self.SetLabel(self._caption)
		wd = {True: self.Parent.Width, False: -1}[self.WordWrap]
		self.Wrap(wd)
#		if plat == "Win":
#			self.Width, self.Height = self.GetBestSize().Get()
#			self.Parent.layout()
#		elif plat == "Mac":
#			self.Parent.layout()
#			self.SetLabel(self._caption)
#			self.Wrap(self.Width)
		self._inResizeEvent = False
		dabo.ui.callAfterInterval(50, self.Parent.unlockDisplayAll)


	# property get/set functions

	def _getAutoResize(self):
		return not self._hasWindowStyleFlag(wx.ST_NO_AUTORESIZE)

	def _setAutoResize(self, value):
		self._delWindowStyleFlag(wx.ST_NO_AUTORESIZE)
		if not value:
			self._addWindowStyleFlag(wx.ST_NO_AUTORESIZE)


	def _getFontBold(self):
		return super(dLabel, self)._getFontBold()

	def _setFontBold(self, val):
		super(dLabel, self)._setFontBold(val)
		if self._constructed():
			# This will force an auto-resize
			self.SetLabel(self.GetLabel())


	def _getFontFace(self):
		return super(dLabel, self)._getFontFace()

	def _setFontFace(self, val):
		super(dLabel, self)._setFontFace(val)
		if self._constructed():
			# This will force an auto-resize
			self.SetLabel(self.GetLabel())


	def _getFontItalic(self):
		return super(dLabel, self)._getFontItalic()

	def _setFontItalic(self, val):
		super(dLabel, self)._setFontItalic(val)
		if self._constructed():
			# This will force an auto-resize
			self.SetLabel(self.GetLabel())


	def _getFontSize(self):
		return super(dLabel, self)._getFontSize()

	def _setFontSize(self, val):
		super(dLabel, self)._setFontSize(val)
		if self._constructed():
			# This will force an auto-resize
			self.SetLabel(self.GetLabel())


	def _getWordWrap(self):
		return self._wordWrap

	def _setWordWrap(self, val):
		if self._constructed():
			self._wordWrap = val
			if val:
				# Make sure AutoResize is False.
				if self.AutoResize:
					#dabo.info.write(_("Setting AutoResize to False since WordWrap is True"))
					self.AutoResize = False
		else:
			self._properties["WordWrap"] = val


	# property definitions follow:
	AutoResize = property(_getAutoResize, _setAutoResize, None,
			_("""Specifies whether the length of the caption determines
			the size of the label. This cannot be True if WordWrap is
			also set to True. Default=True.  (bool)""") )

	FontBold = property(_getFontBold, _setFontBold, None,
			_("Sets the Bold of the Font (int)") )

	FontFace = property(_getFontFace, _setFontFace, None,
			_("Sets the face of the Font (int)") )

	FontItalic = property(_getFontItalic, _setFontItalic, None,
			_("Sets the Italic of the Font (int)") )

	FontSize = property(_getFontSize, _setFontSize, None,
			_("Sets the size of the Font (int)") )

	WordWrap = property(_getWordWrap, _setWordWrap, None,
			_("""When True, the Caption is wrapped to the Width.
			If this is set to True, AutoResize must be False.
			Default=False  (bool)"""))


	DynamicFontBold = makeDynamicProperty(FontBold)
	DynamicFontFace = makeDynamicProperty(FontFace)
	DynamicFontItalic = makeDynamicProperty(FontItalic)
	DynamicFontSize = makeDynamicProperty(FontSize)
	DynamicWordWrap = makeDynamicProperty(WordWrap)


class _dLabel_test(dLabel):
	def initProperties(self):
		self.FontBold = True
		self.Alignment = "Center"
		self.ForeColor = "Red"
		self.Width = 300
		self.Caption = "My God, it's full of stars! " * 22
		self.WordWrap = False


if __name__ == "__main__":
	class LabelTestForm(dabo.ui.uiwx.dForm):
		def afterInit(self):
			pnl = dabo.ui.dPanel(self)
			self.Sizer.append1x(pnl)
			sz = pnl.Sizer = dabo.ui.dSizer("v")
			lbl = dabo.ui.dLabel(pnl, Caption="This label does not have WordWrap" * 20,
					WordWrap=False)
			sz.append1x(lbl)
			lbl = dabo.ui.dLabel(pnl, Caption="This label has WordWrap! " * 20,
					WordWrap=True)
			sz.append1x(lbl)
			dabo.ui.callAfter(self.layout)

	app = dabo.dApp(MainFormClass=LabelTestForm)
	app.start()

#	import test
#	test.Test().runTest(_dLabel_test)
