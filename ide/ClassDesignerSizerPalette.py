# -*- coding: utf-8 -*-
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
dui = dabo.ui
from dabo.dLocalize import _
import dabo.dEvents as dEvents
from ClassDesignerComponents import LayoutSpacerPanel

class ContentBoxSizerPanel(dui.dPanel):
	def afterInit(self):
		sz = dui.dGridSizer(VGap=5, HGap=8, MaxCols=2)
		lbl = dui.dLabel(self, Caption=_("Border"))
		ctl = dui.dSpinner(self, DataField="Sizer_Border", Max=999)
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("Expand"))
		ctl = dui.dCheckBox(self, DataField="Sizer_Expand")
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("Proportion"))
		ctl = dui.dSpinner(self, DataField="Sizer_Proportion")
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("HAlign"))
		ctl = dui.dDropdownList(self, DataField="Sizer_HAlign",
				Choices=["Left", "Right", "Center"])
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("VAlign"))
		ctl = dui.dDropdownList(self, DataField="Sizer_VAlign",
				Choices=["Top", "Bottom", "Middle"])
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("Spacing"))
		ctl = dui.dSpinner(self, DataField="Spacing", Max=999)
		lbl.DynamicEnabled = ctl.DynamicEnabled = self.checkIfSpacer
		sz.append(lbl, halign="right")
		sz.append(ctl)

		self.Sizer = dui.dSizer("v")
		self.Sizer.append1x(sz, border=20,
				borderSides=("left", "right", "bottom"))
		self.Sizer.appendSpacer(20)

	def checkIfSpacer(self):
		return isinstance(self.Form.currObj, LayoutSpacerPanel)


class ContentGridSizerPanel(dui.dPanel):
	def afterInit(self):
		sz = dui.dGridSizer(VGap=5, HGap=8, MaxCols=2)
		lbl = dui.dLabel(self, Caption=_("Border"))
		ctl = dui.dSpinner(self, DataField="Sizer_Border", Max=999)
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("Expand"))
		ctl = dui.dCheckBox(self, DataField="Sizer_Expand")
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("ColExpand"))
		ctl = dui.dCheckBox(self, DataField="Sizer_ColExpand")
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("RowExpand"))
		ctl = dui.dCheckBox(self, DataField="Sizer_RowExpand")
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("Proportion"))
		ctl = dui.dSpinner(self, DataField="Sizer_Proportion")
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("ColSpan"))
		ctl = dui.dSpinner(self, DataField="Sizer_ColSpan")
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("RowSpan"))
		ctl = dui.dSpinner(self, DataField="Sizer_RowSpan")
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("HAlign"))
		ctl = dui.dDropdownList(self, DataField="Sizer_HAlign",
				Choices=["Left", "Right", "Center"])
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("VAlign"))
		ctl = dui.dDropdownList(self, DataField="Sizer_VAlign",
				Choices=["Top", "Bottom", "Middle"])
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("Spacing"))
		ctl = dui.dSpinner(self, DataField="Spacing", Max=999)
		lbl.DynamicEnabled = ctl.DynamicEnabled = self.checkIfSpacer
		sz.append(lbl, halign="right")
		sz.append(ctl)

		self.Sizer = dui.dSizer("v")
		self.Sizer.append1x(sz, border=20,
				borderSides=("left", "right", "bottom"))
		self.Sizer.appendSpacer(20)

	def checkIfSpacer(self):
		return isinstance(self.Form.currObj, LayoutSpacerPanel)


class BoxSizerSelfPanel(dui.dPanel):
	def afterInit(self):
		sz = dui.dGridSizer(VGap=5, HGap=8, MaxCols=2)
		lbl = dui.dLabel(self, Caption=_("Orientation"))
		ctl = dui.dDropdownList(self, DataField="Orientation",
				Choices=["Horizontal", "Vertical"])
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("SlotCount"))
		ctl = dui.dSpinner(self, DataField="SlotCount")
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("DefaultBorder"))
		ctl = dui.dSpinner(self, DataField="DefaultBorder", Max=999)
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("DefaultBorderLeft"))
		ctl = dui.dCheckBox(self, DataField="DefaultBorderLeft")
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("DefaultBorderRight"))
		ctl = dui.dCheckBox(self, DataField="DefaultBorderRight")
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("DefaultBorderTop"))
		ctl = dui.dCheckBox(self, DataField="DefaultBorderTop")
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("DefaultBorderBottom"))
		ctl = dui.dCheckBox(self, DataField="DefaultBorderBottom")
		sz.append(lbl, halign="right")
		sz.append(ctl)

		self.Sizer = dui.dSizer("v")
		self.Sizer.append1x(sz, border=20,
				borderSides=("left", "right", "bottom"))
		self.Sizer.appendSpacer(20)


class GridSizerSelfPanel(dui.dPanel):
	def afterInit(self):
		sz = dui.dGridSizer(VGap=5, HGap=8, MaxCols=2)
		lbl = dui.dLabel(self, Caption=_("HGap"))
		ctl = dui.dSpinner(self, DataField="HGap")
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("VGap"))
		ctl = dui.dSpinner(self, DataField="VGap")
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("Rows"))
		ctl = dui.dSpinner(self, DataField="Rows")
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("Columns"))
		ctl = dui.dSpinner(self, DataField="Columns")
		sz.append(lbl, halign="right")
		sz.append(ctl)
		lbl = dui.dLabel(self, Caption=_("MaxDimension"))
		ctl = dui.dDropdownList(self, DataField="MaxDimension",
				Choices=["C", "R"], Value="C")
		sz.append(lbl, halign="right")
		sz.append(ctl)

		self.Sizer = dui.dSizer("v")
		self.Sizer.append1x(sz, border=20,
				borderSides=("left", "right", "bottom"))
		self.Sizer.appendSpacer(20)


class SizerInfoFrame(dui.dPageFrameNoTabs):
	boxClass = dui.dPanel
	gridClass = dui.dPanel
	def afterInit(self):
		self.blankPage = self.appendPage(dui.dPanel)
		self.blankPage.Sizer = dui.dSizer("v")
		self.boxPage = self.appendPage(self.boxClass)
		self.gridPage = self.appendPage(self.gridClass)

	def layout(self):
		super(SizerInfoFrame, self).layout()
		pg = self.SelectedPage
		try:
			if pg is not self.blankPage:
				dui.callAfter(pg.fitToSizer)
# 				w, h = pg.Size
# 				self.Size = (w+40, h+40)
		except AttributeError:
			# blankPage hasn't been created yet
			pass


class SizerContentFrame(SizerInfoFrame):
	boxClass = ContentBoxSizerPanel
	gridClass = ContentGridSizerPanel

	def setFromObject(self, obj):
		try:
			csz = obj.ControllingSizer
		except AttributeError:
			csz = None
		if csz is None:
			self.SelectedPage = self.blankPage
		elif isinstance(csz, dui.dGridSizer):
			self.SelectedPage = self.gridPage
		else:
			self.SelectedPage = self.boxPage

		self.Visible = (obj is not None)
		self.update()
		self.SelectedPage.setAll("DataSource", obj, filt="Enabled is True")
		#dabo.ui.callAfterInterval(100, self.layout)
		self.layout()


class SizerSelfFrame(SizerInfoFrame):
	boxClass = BoxSizerSelfPanel
	gridClass = GridSizerSelfPanel

	def setFromObject(self, obj):
		if isinstance(obj, dui.dGridSizer):
			self.SelectedPage = self.gridPage
		elif isinstance(obj, dui.dSizer):
			self.SelectedPage = self.boxPage
		else:
			self.SelectedPage = self.blankPage
		self.Visible = isinstance(obj, (dui.dGridSizer, dui.dSizer,
				dui.dBorderSizer))
		self.SelectedPage.setAll("DataSource", obj, filt="Enabled is True")
		self.update()
		self.layout()


class AbstractSizerPanel(dui.dPanel):
	pgfClass = None

	def afterInit(self):
		self.Sizer = dui.dBorderSizer(self, "v", Caption=self._cap)
		self.pgf = self.pgfClass(self)
		self.Sizer.append(self.pgf, halign="center")
		self.DynamicVisible = self.notBlank

	def notBlank(self):
		return self.pgf.SelectedPage is not self.pgf.blankPage

	def layout(self, resetMin=True):
		super(AbstractSizerPanel, self).layout(resetMin)
		self.Size = self.pgf.Size


class SizerContentPanel(AbstractSizerPanel):
	pgfClass = SizerContentFrame
	_cap = _("Object Settings")


class SizerSelfPanel(AbstractSizerPanel):
	pgfClass = SizerSelfFrame
	_cap = _("Sizer Settings")


class SizerPaletteForm(dui.dToolForm):
	def __init__(self, *args, **kwargs):
		if self.Application.Platform == "GTK":
			# There are some serious issues with resizing the dToolForm on Gtk,
			# so use a plain form instead
			SizerPaletteForm.__bases__ = (dui.dForm,)
			kwargs["ShowStatusBar"] = False
			kwargs["ShowMaxButton"] = False
			kwargs["ShowMinButton"] = False
			kwargs["TinyTitleBar"] = True
		super(SizerPaletteForm, self).__init__(*args, **kwargs)

	def beforeInit(self):
		self.MenuBarClass = None

	def afterInit(self):
		self.currObj = None
		self.inFitToSizer = False
		self.MinimumSize = (200, 100)
		self.Sizer = dui.dSizer("V")
		self.mainPanel = mp = dui.dPanel(self)
		self.Sizer.append1x(mp)
		mp.Sizer = sz = dui.dSizer("H")
		scpnl = SizerContentPanel(mp)
		self.contentFrame = scpnl.pgf
		sspnl = SizerSelfPanel(mp)
		self.sizerFrame = sspnl.pgf
		sz.append(scpnl, halign="center", border=10)
		sz.append(sspnl, halign="center", border=10)
		self.layout()

	def select(self, objs):
		if not self.Visible:
			return
		if (len(objs) > 1) or not objs:
			self.contentFrame.setFromObject(None)
			self.sizerFrame.setFromObject(None)
			self.layout()
			return
		obj = objs[0]
		self.currObj = obj
		self.contentFrame.setFromObject(obj)
		self.sizerFrame.setFromObject(obj)
		self.layout()
		dabo.ui.callAfter(self.fitToSizer, extraHeight=10)
		self.update()

	def layout(self):
		if self.inFitToSizer:
			return
		dui.callAfterInterval(100, self._delayedLayout)
	def _delayedLayout(self):
		self.lockDisplay()
		super(SizerPaletteForm, self).layout()

		self.inFitToSizer = True
		self.fitToSizer()
		self.inFitToSizer = False
		self.unlockDisplay()

	def _getController(self):
		try:
			return self._controller
		except AttributeError:
			self._controller = self.Application
			return self._controller

	def _setController(self, val):
		if self._constructed():
			self._controller = val
		else:
			self._properties["Controller"] = val

	Controller = property(_getController, _setController, None,
			_("Object to which this one reports events  (object (varies))"))

