# -*- coding: utf-8 -*-
import wx
import wx.lib.foldpanelbar as fpb
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlMixin as dcm
import dabo.dEvents as dEvents
import dabo.dColors as dColors
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


class dFoldPanel(dcm.dControlMixin, fpb.FoldPanelItem):
	def __init__(self, parent, caption=None, collapsed=None, properties=None, 
			attProperties=None, *args, **kwargs):
		
		self._baseClass = dFoldPanel
		preClass = fpb.FoldPanelItem
		self._widthAlreadySet = self._heightAlreadySet = True

		# This needs to be set *after* the panel is added to its parent
		collapsed = self._extractKey(attProperties, "Collapsed", None)
		if collapsed is not None:
			collapsed = (collapsed == "True")
		else:
			collapsed = self._extractKey((kwargs, properties), "Collapsed", None)
			if collapsed is None:
				# They might have passed it as 'Expanded'
				collapsed = not self._extractKey((kwargs, properties), "Expanded", True)
		
		cbstyle = self._extractKey((kwargs, properties), "cbstyle", None)
		if cbstyle is None:
			kwargs["cbstyle"] = fpb.CaptionBarStyle()
		
		if isinstance(parent, fpb.FoldPanelBar):
			# Items have to be added to the internal panel instead
			self._bar = parent
			parent = parent._foldPanel
		else:
			# Must have been created from the parent control
			self._bar = parent.GetParent()

		self._captionForeColor = "black"
		self._barStyles = ("Borderless", "BorderOnly", 
				"FilledBorder", "VerticalFill", "HorizontalFill")
		self._barStylesLow = ("borderless", "borderonly", 
				"filledborder", "verticalfill", "horizontalfill")
		self._barStyleConstants = {"nostyle" : fpb.CAPTIONBAR_NOSTYLE,
				"verticalfill" : fpb.CAPTIONBAR_GRADIENT_V,
				"horizontalfill" : fpb.CAPTIONBAR_GRADIENT_H,
				"borderless" : fpb.CAPTIONBAR_SINGLE,
				"borderonly" : fpb.CAPTIONBAR_RECTANGLE,
				"filledborder" : fpb.CAPTIONBAR_FILLED_RECTANGLE}

		dcm.dControlMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)

		self._bar.append(self)
		self._bar.RedisplayFoldPanelItems()
		if collapsed is not None:
			self.Collapsed = collapsed
		# Enable detection of clicks on the caption bar
		self._captionBar.Bind(wx.EVT_LEFT_UP, self.__onWxCaptionClick)
	

	def GetBestSize(self):
		ret = super(dFoldPanel, self).GetBestSize()
		sibCount = len(self.GetParent().GetChildren())
		prnt = self.GetParent()
		if prnt:
			psz = prnt.GetSize()
			pWd, pHt = psz.GetWidth(), psz.GetHeight()
			capHt = self.CaptionHeight * (sibCount-1)
			if ret.GetWidth() > pWd:
				ret.SetWidth(pWd)
			if not self.IsExpanded():
				ret.SetHeight(self.CaptionHeight)
			else:
				if self.Parent.Singleton:
					ret.SetHeight(pHt - capHt)
				else:
					if ret.GetHeight() > pHt - capHt:
						ret.SetHeight(pHt - capHt)
		return ret
		
		
	def onChildBorn(self, evt):
		self._bar.lockDisplay()
		ch = evt.child
		self._bar.AddFoldPanelWindow(self, ch)
		self._bar.RefreshPanelsFrom(self)
		self._bar.unlockDisplay()
	
	
	def appendSeparator(self, color=None):
		"""This draws a separator line on the panel"""
		if color is None:
			color = "black"
		self.AddSeparator(self._getWxColour(color))
		
	
	def layout(self):
		""" Wrap the wx version of the call, if possible. """
		self.Layout()
		try:
			# Call the Dabo version, if present
			self.Sizer.layout()
		except:
			pass
		if self.Application.Platform == "Win":
			self.refresh()


	def __onWxCaptionClick(self, evt):
		self.raiseEvent(dEvents.FoldPanelCaptionClick, evt)
				

	def _getBarColor1(self):
		return self._barColor1

	def _setBarColor1(self, val):
		color = self._getWxColour(val)
		self._barColor1 = val
		style = self._captionBar.GetCaptionStyle()
		style.SetFirstColour(color)
		self._captionBar.SetCaptionStyle(style)


	def _getBarColor2(self):
		return self._barColor2

	def _setBarColor2(self, val):
		color = self._getWxColour(val)
		self._barColor2 = val
		style = self._captionBar.GetCaptionStyle()
		style.SetSecondColour(color)
		self._captionBar.SetCaptionStyle(style)


	def _getBarStyle(self):
		return self._barStyle

	def _setBarStyle(self, val):
		if val.lower().strip() not in self._barStylesLow:
			dabo.errorLog.write(_("Unknown BarStyle passed: %s. BarStyle must be one of: %s")
					% (val, ", ".join(self._barStyles)))
		else:
			self._barStyle = val
			# Apply it
			style = self._captionBar.GetCaptionStyle()
			style.SetCaptionStyle(self._barStyleConstants[val.lower().strip()])
			self._captionBar.SetCaptionStyle(style)
			

	def _getCaption(self):
		return self._captionBar._caption

	def _setCaption(self, val):
		self._captionBar._caption = val
		self.refresh()
		

	def _getCaptionForeColor(self):
		return self._captionForeColor

	def _setCaptionForeColor(self, val):
# 		dabo.infoLog.write("CaptionForeColor - Not implemented yet")
		self._captionForeColor = val
		style = self._captionBar.GetCaptionStyle()
		style.SetCaptionColour(self._getWxColour(val))
		self._captionBar.SetCaptionStyle(style)


	def _getCaptionHeight(self):
		return self._captionBar.GetSize()[1]


	def _getCollapsed(self):
		return not self.IsExpanded()

	def _setCollapsed(self, val):
		if val:
			self._bar.Collapse(self)
		else:
			self._bar.Expand(self)


	def _getExpanded(self):
		return self.IsExpanded()

	def _setExpanded(self, val):
		if val:
			self._bar.Expand(self)
		else:
			self._bar.Collapse(self)


	def _getParent(self):
		return self._bar


	BarColor1 = property(_getBarColor1, _setBarColor1, None,
			_("Main color for the caption bar  (dColor)"))
	
	BarColor2 = property(_getBarColor2, _setBarColor2, None,
			_("Secondary color for the caption bar. Only used in gradients  (dColor)"))
	
	BarStyle = property(_getBarStyle, _setBarStyle, None,
			_(""""Determines how the bar containing the caption 
			for this panel is drawn. (str)
			
			Can be one of the following:
				Borderless		(no border, just a plain fill color; default)
				BorderOnly		(simple border, no fill color)
				FilledBorder	(combination of the two above)
				VerticalFill		(vertical gradient fill, using the two caption colors)
				HorizontalFill		(horizontal gradient fill, using the two caption colors)
			"""))

	Caption = property(_getCaption, _setCaption, None,
			_("Caption displayed on the panel bar  (str)"))
	
	CaptionForeColor = property(_getCaptionForeColor, _setCaptionForeColor, None,
			_("Text color of the caption bar  (str or tuple)"))
	
	CaptionHeight = property(_getCaptionHeight, None, None,
			_("Height of the caption bar. Read-only  (int)"))
	
	Collapsed = property(_getCollapsed, _setCollapsed, None,
			_("Is the panel's contents hidden?  (bool)"))
	
	Expanded = property(_getExpanded, _setExpanded, None,
			_("Is the panel's contents visible?  (bool)"))

	Parent = property(_getParent, None, None, 
			_("Reference to the containing dFoldPanelBar."))

	DynamicBarColor1 = makeDynamicProperty(BarColor1)
	DynamicBarColor2 = makeDynamicProperty(BarColor2)
	DynamicBarStyle = makeDynamicProperty(BarStyle)
	DynamicCaption = makeDynamicProperty(Caption)
	DynamicCaptionForeColor = makeDynamicProperty(CaptionForeColor)
	DynamicCollapsed = makeDynamicProperty(Collapsed)
	DynamicExpanded = makeDynamicProperty(Expanded)



	
class dFoldPanelBar(dcm.dControlMixin, wx.lib.foldpanelbar.FoldPanelBar):
	"""Creates a control consisting of several panels that can be 
	hidden or revealed by clicking on their 'caption bar'.
	
	This allows you to collapse each panel down to its caption bar,
	which either remains in place or drops to the bottom.
	"""	
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dFoldPanelBar
		preClass = fpb.FoldPanelBar
		self._singleClick = False
		self._collapseToBottom = False
		self._singleton = False
		# Flag to indicate whether panels are being expanded
		# or collapsed due to internal rules for Singleton format.
		self.__inSingletonProcess = False
		# Flag to track the currently expanded panel in Singleton format.
		self.__openPanel = None
		
		dcm.dControlMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)

		self._setInitialOpenPanel()
		self.bindEvent(dEvents.FoldPanelChange, self.__onFoldPanelChange)
	

	def append(self, pnl):
		pos = 0
		if len(self._panels) > 0:
			pos = self._panels[-1].GetItemPos() + self._panels[-1].GetPanelLength()
		pnl.Reposition(pos)
		self._panels.append(pnl)
		self.raiseEvent(dEvents.FoldPanelChange, 
				self._createCapBarEvt(pnl))
		pnl.bindEvent(dEvents.FoldPanelCaptionClick, 
				self.onFoldPanelCaptionClick, pnl)


	def onFoldPanelCaptionClick(self, evt):
		if self.SingleClick:
			obj = evt.EventObject
			obj.Expanded = not obj.Expanded


	def _createCapBarEvt(self, pnl):
		evt = fpb.CaptionBarEvent(fpb.wxEVT_CAPTIONBAR)
		cap = pnl._captionBar
		evt.SetId(cap.GetId())
		evt.SetEventObject(cap)
		evt.SetBar(cap)
		return evt

		
	def Collapse(self, pnl):
		if pnl.Collapsed:
			# nothing to do here
			return
		super(dFoldPanelBar, self).Collapse(pnl)
		self.raiseEvent(dEvents.FoldPanelChange, 
				self._createCapBarEvt(pnl))

	
	def Expand(self, pnl):
		if pnl.Expanded:
			# nothing to do here
			return
		super(dFoldPanelBar, self).Expand(pnl)
		self.raiseEvent(dEvents.FoldPanelChange, 
				self._createCapBarEvt(pnl))

	# Throw in Dabo-style wrapper names
	expand = Expand
	collapse = Collapse


	def collapseAll(self):
		for pnl in self._panels:
			pnl.Collapsed = True
	
	
	def expandAll(self):
		for pnl in self._panels:
			pnl.Expanded = True


	def refresh(self):
		super(dFoldPanelBar, self).refresh()
		if self.CollapseToBottom:
			rect = self.RepositionCollapsedToBottom()
			vertical = self.IsVertical()
			if vertical and rect.GetHeight() > 0 or not vertical and rect.GetWidth() > 0:
				self.RefreshRect(rect)
			

	def layout(self):
		""" Wrap the wx version of the call, if possible. """
		if not self:
			# The object may have already been released.
			return
		self.Layout()

	
	def onResize(self, evt):
		self.sizePanelHeights()
		

	def _setInitialOpenPanel(self):
		"""When self.Singleton is true, ensures that one panel is
		open.
		"""
		if not self.Singleton:
			return
		# Make sure that one panel is open. If not, open the first.
		# If there is more than one panel open, close all but the 
		# first open panel.
		if len(self._panels) == 0:
			return
		self.__inSingletonProcess = True
		found = False
		for pnl in self._panels:
			if pnl.Expanded:
				if found:
					pnl.Expanded = False
				else:
					self.__openPanel = pnl
					found = True
		if not found:
			self._panels[0].Expanded = True	
			self.__openPanel = self._panels[0]
		self.__inSingletonProcess = False
		
		
	def __onFoldPanelChange(self, evt):
		"""This ensures that one and only one panel remains expanded
		when the control is in Singleton mode.
		"""
		if not self.Singleton:
			self.sizePanelHeights(force=True)
			return
		if self.__inSingletonProcess:
			# The panel is changing due to this method, so ignore
			# it to avoid infinite loops.
			return
		self.__inSingletonProcess = True
		# This is in response to an external request to a panel
		# being expanded or collapsed.
		curr = self.__openPanel
		evtPanel = evt.panel
		isOpening = evt.expanded
		changing = curr is not evtPanel
		if isOpening:
			if curr is not None:
				if curr is not evtPanel:
					# Close the current one
					curr.Collapsed = True
			self.__openPanel = evtPanel
		else:
			# The panel is closing. If it was the current panel, 
			# keep it open.
			if curr is None:
				# This is the first panel being added; keep it open
				evtPanel.Expanded = True
				self.__openPanel = evtPanel
			elif curr is evtPanel:
				curr.Expanded = True
		if changing:
			self.layout()
			dabo.ui.callAfter(self.sizePanelHeights)
			self.refresh()
		self.__inSingletonProcess = False

	
	def sizePanelHeights(self, force=False):
		"""Control the heights of the panels. Originally I thought we only needed
		this when running in Singleton mode, but now it seems better to run this
		in all modes.
		"""
#- 		if not self.Singleton and not force:
#- 			return
		# Size the open panel to fill the space
		top = 0
		pnlList = self._panels[:]
		if self.CollapseToBottom:
			# Sort so that the first panel is the expanded one.
			pnlList.sort(lambda x, y: cmp(x.Collapsed, y.Collapsed))
		fp = pnlList[0]		
		fp.Reposition(0)
		self.RefreshPanelsFrom(fp)
		for pnl in pnlList:
			if not pnl.Expanded:
				pnl.Height = pnl.CaptionHeight
			else:
				# Make the panel that big, plus the height of the caption
				capHt = pnl.CaptionHeight * (len(self._panels) -1)
				pnl.Height = self.Height - capHt
			pnl.Top = top
			pnl.layout()
			top += pnl.Height
		dabo.ui.callAfter(self.layout)
		

	def _getChildren(self):
		return self._panels
	
	
	def _getCollapseToBottom(self):
		return bool(self._extraStyle & fpb.FPB_COLLAPSE_TO_BOTTOM)

	def _setCollapseToBottom(self, val):
		self._collapseToBottom = val
		if val:
			self._extraStyle = self._extraStyle | fpb.FPB_COLLAPSE_TO_BOTTOM
		else:
			self._extraStyle = self._extraStyle &  ~fpb.FPB_COLLAPSE_TO_BOTTOM
		if self._panels:
			fp = self._panels[0]
			fp.Reposition(0)
			self.RefreshPanelsFrom(fp)
			self.sizePanelHeights(force=True)
			self.layout()
			

	def _getSingleClick(self):
		return self._singleClick

	def _setSingleClick(self, val):
		self._singleClick = val


	def _getSingleton(self):
		return self._singleton

	def _setSingleton(self, val):
		self._singleton = val
		# Make sure that only one panel is open
		self._setInitialOpenPanel()


	Children = property(_getChildren, None, None,
			_("List of all panels in the control  (list))"))
			
	CollapseToBottom = property(_getCollapseToBottom, _setCollapseToBottom, None,
			_("When True, all collapsed panels are displayed at the bottom  (bool)"))
	
	SingleClick = property(_getSingleClick, _setSingleClick, None,
			_("""When True, a single click on the caption bar toggles the 
			expanded/collapsed state  (bool)"""))
	
	Singleton = property(_getSingleton, _setSingleton, None,
			_("When True, one and only one panel at a time will be expanded  (bool)"))


	DynamicCollapseToBottom = makeDynamicProperty(CollapseToBottom)
	DynamicSingleClick = makeDynamicProperty(SingleClick)
	DynamicSingleton = makeDynamicProperty(Singleton)


if __name__ == "__main__":
	class TestForm(dabo.ui.dForm):
		def afterInit(self):
			dFoldPanelBar(self, RegID="FoldBar")
			self.Sizer.append1x(self.FoldBar)
			self.p1 = dabo.ui.dFoldPanel(self.FoldBar, Caption="First", 
					BackColor="orange")
			self.p2 = dabo.ui.dFoldPanel(self.FoldBar, Caption="Second", 
					Collapsed=True, BarStyle="FilledBorder", 
					BarColor1="SpringGreen", BackColor="lightgreen")
			self.p3 = dabo.ui.dFoldPanel(self.FoldBar, Caption="Third",
					BarStyle="BorderOnly", BackColor="bisque")
			
			pnl = dabo.ui.dPanel(self.p1)
			self.p1.Sizer = dabo.ui.dSizer("v")
			self.p1.Sizer.appendSpacer(self.p1.CaptionHeight)
			self.p1.Sizer.append1x(pnl)
			pnl.Sizer = dabo.ui.dSizer("v")
			btn = dabo.ui.dButton(pnl, Caption="Change Bar 1 Style")
			pnl.Sizer.append(btn)
			btn.bindEvent(dEvents.Hit, self.onBtn)
			dabo.ui.dLabel(self.p2, Caption="Two Step", FontItalic=True,
					FontSize=24)
			dabo.ui.dLabel(self.p3, Caption="Three Strikes")
			
			hsz = dabo.ui.dSizer("h")
			btnCollapse = dabo.ui.dButton(self, Caption="Collapse All")
			btnCollapse.bindEvent(dEvents.Hit, self.onCollapseAll)
			btnExpand = dabo.ui.dButton(self, Caption="Expand All")
			btnExpand.bindEvent(dEvents.Hit, self.onExpandAll)
			hsz.append(btnCollapse)
			hsz.appendSpacer(10)
			hsz.append(btnExpand)
			hsz.appendSpacer(10)
			chkSingleton = dabo.ui.dCheckBox(self, Caption="Singleton Style", 
					DataSource="self.Form.FoldBar", DataField="Singleton")
			chkSingle = dabo.ui.dCheckBox(self, Caption="Single Click to Toggle", 
					DataSource="self.Form.FoldBar", DataField="SingleClick")
			chkBottom = dabo.ui.dCheckBox(self, Caption="Collapsed Panels To Bottom", 
					DataSource="self.Form.FoldBar", DataField="CollapseToBottom")
			self.Sizer.appendSpacer(10)
			vsz = dabo.ui.dSizer("v")
			vsz.append(chkSingleton)
			vsz.append(chkSingle)
			vsz.append(chkBottom)
			hsz.append(vsz)
			self.Sizer.append(hsz, 0, halign="center", border=10)
			self.layout()


		def onBtn(self, evt):
			self.p1.BarStyle = "HorizontalFill"
			self.p1.BarColor1 = "yellow"
			self.p1.BarColor2 = "red"
			obj = evt.EventObject
			obj.Enabled = False
			self.p1.appendSeparator("white")
			
			lbl = dabo.ui.dLabel(obj.Parent, Caption="Changed!", 
					FontItalic=True, FontSize=48)
			obj.Parent.Sizer.append(lbl)
			obj.Parent.layout()
			

		def onCollapseAll(self, evt):
			self.FoldBar.collapseAll()
			
		def onExpandAll(self, evt):
			self.FoldBar.expandAll()
			
	
	app = dabo.dApp()
	app.MainFormClass = TestForm
	app.start()


