# -*- coding: utf-8 -*-
import wx
import dabo
import dabo.dEvents as dEvents
from dabo.dLocalize import _

from dabo.ui import makeDynamicProperty
if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
from alignmentMixin import AlignmentMixin


class dLabel(cm.dControlMixin, AlignmentMixin, wx.StaticText):
	"""Creates a static label, to make a caption for another control, for example."""
	_layout_on_set_caption = True

	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dLabel
		self._wordWrap = False
		self._inResizeEvent = False
		self._resetAutoResize = True
		preClass = wx.PreStaticText
		cm.dControlMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)
		self.bindEvent(dEvents.Resize, self.__onResize)


	def __onResize(self, evt):
		"""
		Event binding is set when WordWrap=True. Tell the label
		to wrap to its current width.
		"""
		if self.WordWrap:
			if self._inResizeEvent:
				return
			self._inResizeEvent = True
			dabo.ui.callAfterInterval(100, self.__resizeExecute)


	def __resizeExecute(self):
		# We need to set the caption to the internally-saved caption, since
		# WordWrap can introduce additional linefeeds.
		try:
			self.Parent.lockDisplay()
		except dabo.ui.deadObjectException:
			# Form is being destroyed; bail
			return
		self.SetLabel(self._caption)
		wd = {True: self.Width, False: -1}[self.WordWrap]
		self.Wrap(wd)
		dabo.ui.callAfterInterval(50, self.__endResize)


	def __endResize(self):
		"""
		To prevent infinite loops while resizing, the _inResizeEvent
		flag must be reset outside of the execution method.
		"""
		self.Parent.unlockDisplayAll()
		self._inResizeEvent = False


	# property get/set functions
	def _getAutoResize(self):
		return not self._hasWindowStyleFlag(wx.ST_NO_AUTORESIZE)

	def _setAutoResize(self, val):
		self._delWindowStyleFlag(wx.ST_NO_AUTORESIZE)
		if not val:
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
			changed = (self._wordWrap != val)
			if not changed:
				return
			self._wordWrap = val
			if val:
				# Make sure AutoResize is False.
				if self.AutoResize:
					self._resetAutoResize = True
					self.AutoResize = False
				try:
					dabo.ui.callAfter(self.Parent.layout)
				except AttributeError:
					# Parent has no layout() method.
					pass
			else:
				# reset the value
				self.AutoResize = self._resetAutoResize
			self.__resizeExecute()
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
			_("""When True, the Caption is wrapped to the Width. Note
			that the control must have sufficient Height to display any
			wrapped text.
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
	from dabo.dApp import dApp
	class LabelTestForm(dabo.ui.uiwx.dForm):
		def afterInit(self):
			self.Caption = "dLabel Test"
			pnl = dabo.ui.dPanel(self)
			self.Sizer.append1x(pnl)
			sz = pnl.Sizer = dabo.ui.dSizer("v")
			sz.appendSpacer(25)
			self.sampleLabel = dabo.ui.dLabel(pnl, Caption="This label has a very long Caption. " * 20,
					WordWrap=False)
			self.wrapControl = dabo.ui.dCheckBox(pnl, Caption="WordWrap",
					DataSource=self.sampleLabel, DataField="WordWrap")
			sz.append(self.wrapControl, halign="center", border=20)
			sz.append1x(self.sampleLabel, border=10)
			self.update()
			dabo.ui.callAfterInterval(200, self.layout)

	app = dApp(MainFormClass=LabelTestForm)
	app.start()
