import wx
import wx.lib.foldpanelbar as fpb
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlMixin as dcm
import dabo.dEvents as dEvents
import dabo.dColors as dColors
from dabo.dLocalize import _


class dFoldPanel(fpb.FoldPanelItem, dcm.dControlMixin):
	def __init__(self, parent, caption=None, collapsed=None, 
			properties=None, *args, **kwargs):
		
		self._baseClass = dFoldPanel
		preClass = fpb.FoldPanelItem

		# This needs to be set *after* the panel is added to its parent
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

		dcm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

		self._bar.append(self)
		self._bar.RedisplayFoldPanelItems()
		if collapsed is not None:
			self.Collapsed = collapsed
				

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
		
		
	def _getWxColour(self, val):
		"""Convert Dabo colors to wx.Colour objects"""
		ret = None
		if isinstance(val, basestring):
			try:
				val = dColors.colorTupleFromName(val)
			except: pass
		if isinstance(val, tuple):
			ret = wx.Colour(*val)
		return ret
		
		
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
	
	Collapsed = property(_getCollapsed, _setCollapsed, None,
			_("Is the panel's contents hidden?  (bool)"))
	
	Expanded = property(_getExpanded, _setExpanded, None,
			_("Is the panel's contents visible?  (bool)"))



	
class dFoldPanelBar(wx.lib.foldpanelbar.FoldPanelBar, dcm.dControlMixin):
	"""Creates a control consisting of several panels that can be 
	hidden or revealed by clicking on their 'caption bar'.
	
	This allows you to collapse each panel down to its caption bar,
	which either remains in place or drops to the bottom.
	"""	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dFoldPanelBar
		preClass = fpb.FoldPanelBar
		dcm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
		

	def append(self, pnl):
		pos = 0
		if len(self._panels) > 0:
			pos = self._panels[-1].GetItemPos() + self._panels[-1].GetPanelLength()
		pnl.Reposition(pos)
		self._panels.append(pnl)
	
	
	def collapseAll(self):
		for pnl in self._panels:
			pnl.Collapsed = True
	
	
	def expandAll(self):
		for pnl in self._panels:
			pnl.Expanded = True




if __name__ == "__main__":

	class TestForm(dabo.ui.dForm):
		def afterInit(self):
			self.bar = dabo.ui.dFoldPanelBar(self)
			self.Sizer.append1x(self.bar)
			self.p1 = dabo.ui.dFoldPanel(self.bar, Caption="First")
			self.p2 = dabo.ui.dFoldPanel(self.bar, Caption="Second", 
					Collapsed=True, BarStyle="FilledBorder", 
					BarColor1="SpringGreen")
			self.p3 = dabo.ui.dFoldPanel(self.bar, Caption="Third",
					BarStyle="BorderOnly")
			
			btn = dabo.ui.dButton(self.p1, Caption="Change Bar 1 Style")
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
			self.Sizer.appendSpacer(10)
			self.Sizer.append(hsz, 0, halign="center")

		def onBtn(self, evt):
			self.p1.BarStyle = "HorizontalFill"
			self.p1.BarColor1 = "yellow"
			self.p1.BarColor2 = "red"
			evt.EventObject.Enabled = False
			self.p1.appendSeparator("white")
			dabo.ui.dLabel(self.p1, Caption="Changed!", FontItalic=True,
					FontSize=48)
			

		def onCollapseAll(self, evt):
			self.bar.collapseAll()
			
		def onExpandAll(self, evt):
			self.bar.expandAll()
			
	
	app = dabo.dApp()
	app.MainFormClass = TestForm
	app.start()
			
			
			
			