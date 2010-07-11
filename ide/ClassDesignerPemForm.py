# -*- coding: utf-8 -*-
import dabo
from dabo.dLocalize import _
from dabo.lib.utils import ustr
import dabo.dEvents as dEvents
from ClassDesignerPropSheet import PropSheet
from ClassDesignerTreeSheet import TreeSheet
from ClassDesignerMethodSheet import MethodSheet
from ClassDesignerObjectPropertySheet import ObjectPropertySheet
from ClassDesignerComponents import LayoutPanel
from ClassDesignerComponents import LayoutSpacerPanel
from ClassDesignerComponents import LayoutSizer
from ClassDesignerComponents import LayoutGridSizer
import ClassDesignerMenu

if __name__ == "__main__":
	dabo.ui.loadUI("wx")


class PemForm(dabo.ui.dForm):
	"""This form contains the PropSheet, the MethodSheet, and
	the Object Tree.
	"""
	def afterSetMenuBar(self):
		self.ShowStatusBar = False
		ClassDesignerMenu.mkDesignerMenu(self)


	def onMenuOpen(self, evt):
		self.Controller.menuUpdate(evt, self.MenuBar)


	def afterInit(self):
		self._defaultLeft = 610
		self._defaultTop = 50
		self._defaultWidth = 370
		self._defaultHeight = 580

		self.Caption = _("Object Info")
		pnl = dabo.ui.dPanel(self)
		self.Sizer.append1x(pnl)
		sz = pnl.Sizer = dabo.ui.dSizer("v")

		txt = dabo.ui.dTextBox(pnl, ReadOnly=True, RegID="txtObj")
		hsz = dabo.ui.dSizer("h")
		hsz.append1x(txt)
		self.treeBtn = dabo.ui.dToggleButton(pnl, Height=txt.Height,
				Width=txt.Height, Caption="", Picture="downTriangleBlack",
				DownPicture="upTriangleBlack")
		self.treeBtn.bindEvent(dEvents.Hit, self.onToggleTree)
		hsz.append(self.treeBtn)

		brdr = 10
		sz.appendSpacer(brdr)
		sz.DefaultBorderLeft = sz.DefaultBorderRight = True
		sz.DefaultBorder = brdr
		sz.append(hsz, "x")
		sz.appendSpacer(5)

		self.mainPager = mp = dabo.ui.dPageFrameNoTabs(pnl, PageClass=dabo.ui.dPanel)
		mp.PageCount=2
		mp.bindEvent(dEvents.PageChanged, self.onMainPageChanged)
		sz.append1x(mp)
		sz.appendSpacer(brdr)
		self.pemPage = pp = mp.Pages[0]
		self.treePage = tp = mp.Pages[1]
		psz = pp.Sizer = dabo.ui.dSizer("v")
		tsz = tp.Sizer = dabo.ui.dSizer("v")

		dabo.ui.dSlidePanelControl(pp, SingleClick=True, Singleton=True,
				CollapseToBottom=True, RegID="mainContainer")
		psz.append1x(self.mainContainer)
		# This helps restore the sash position on the prop grid page
		self._propSashPct = 80
		# Bind to panel changes
		self.mainContainer.bindEvent(dEvents.SlidePanelChange, self.onPanelChange)
		dabo.ui.dSlidePanel(self.mainContainer, Caption=_("Properties"), RegID="propPage",
				CaptionForeColor="blue")
		dabo.ui.dSlidePanel(self.mainContainer, Caption=_("Methods"), RegID="methodPage",
				CaptionForeColor="blue")
		dabo.ui.dSlidePanel(self.mainContainer, Caption=_("Custom Properties"), RegID="objPropPage",
				CaptionForeColor="blue")

		# Add the PropSheet
		ps = PropSheet(self.propPage, RegID="_propSheet")
		self.propPage.Sizer = dabo.ui.dSizer("v")
		self.propPage.Sizer.appendSpacer(self.propPage.CaptionHeight)
		self.propPage.Sizer.append1x(ps)

		# Create the MethodSheet
		ms = MethodSheet(self.methodPage, RegID="_methodSheet")
		self.methodPage.Sizer = dabo.ui.dSizer("v")
		self.methodPage.Sizer.appendSpacer(self.methodPage.CaptionHeight)
		self.methodPage.Sizer.append1x(ms)
		self._methodList = ms.MethodList

		# Create the tree
		self._tree = TreeSheet(tp)
		tp.Sizer.append1x(self._tree, border=10)

		# Create the Object Properties sheet
		ops = ObjectPropertySheet(self.objPropPage, RegID="_objPropSheet")
		self.objPropPage.Sizer = dabo.ui.dSizer("v")
		self.objPropPage.Sizer.appendSpacer(self.methodPage.CaptionHeight)
		self.objPropPage.Sizer.append1x(ops)

		mp.SelectedPage = pp

		ps.Controller = ms.Controller = self._tree.Controller = ops.Controller = self.Controller
		self.layout()
		dabo.ui.callAfter(self.mainContainer.expand, self.propPage)


	def onToggleTree(self, evt):
		self.mainPager.nextPage()


	def onMainPageChanged(self, evt):
		self.treeBtn.Value = self.mainPager.SelectedPage is self.treePage


	def hideTree(self):
		self.mainPager.SelectedPage = self.pemPage


	def onPanelChange(self, evt):
		if evt.panel is self.propPage:
			try:
				if evt.expanded:
					dabo.ui.setAfter(self._propSheet.mainSplit, "SashPercent", self._propSheet._sashPct)
			except:
				# Probably isn't constructed yet
				pass


	def onResize(self, evt):
		try:
			dabo.ui.callAfter(self.mainContainer.refresh)
		except:
			# 'mainContainer' might not be defined yet, so ignore
			pass


	def showPropPage(self):
		self.mainPager.SelectedPage = self.pemPage
		self.refresh()
		self.propPage.Expanded = True
		self.bringToFront()


	def showTreePage(self):
		self.mainPager.SelectedPage = self.treePage
		self.bringToFront()


	def showMethodsPage(self):
		self.mainPager.SelectedPage = self.pemPage
		self.methodPage.Expanded = True
		self.bringToFront()


	def select(self, obj):
		"""Called when the selected object changes. 'obj' will
		be a list containing either a single object or multiple
		objects. We then need to update the components of this
		form appropriately.
		"""
		mult = len(obj) > 1
		if len(obj) == 0:
			lbl = _(" -none- ")
			ob = None
		else:
			ob = obj[0]
			# If the selected object is an empty sizer slot, the way that this
			# is passed along is a tuple containing the sizer item and its sizer,
			# since there is no way to determine the sizer given the SizerItem.
			isSpacer = isinstance(ob, LayoutSpacerPanel)
			isSlot = isinstance(ob, LayoutPanel) and not isSpacer
			isSizer = isinstance(ob, dabo.ui.dSizerMixin)
			isColumn = isinstance(ob, dabo.ui.dColumn)
			isNode = isinstance(ob, dabo.ui.dTreeView.getBaseNodeClass())
			if isSlot or isSpacer:
				szItem = ob.ControllingSizerItem
				sz = ob.ControllingSizer
			if isSizer:
				sz = ob
			obRest = obj[1:]
			# Determine the 'name' to display
			if mult:
				lbl = _(" -multiple- ")
			else:
				if isSlot or isSizer:
					ornt = sz.Orientation[0].lower()
					if ornt == "h":
						lbl = _("Horizontal")
					elif ornt == "v":
						lbl = _("Vertical")
					else:
						lbl = _("Grid")
					if isSlot:
						lbl += _(" Sizer Slot")
						if ornt in ("r", "c"):
							lbl += ": (%s, %s)" % sz.getGridPos(ob)
					else:
						if isinstance(ob, dabo.ui.dBorderSizer):
							lbl += _(" BorderSizer")
						else:
							lbl += _(" Sizer")
				elif isSpacer:
					spc = ob.Spacing
					if isinstance(sz, dabo.ui.dSizer):
						# We want the first position for vertical; second for horiz.
						isHoriz = sz.Orientation[0].lower() == "h"
						typ = (_("Vertical"), _("Horizontal"))[isHoriz]
					else:
						# Grid spacer; use both
						typ = _("Grid")
					lbl = "%s Spacer - (%s)" % (typ, spc)
				elif isColumn:
					if ob.Visible:
						lbl = "Column %s ('%s')" % (ob.Parent.Columns.index(ob)+1, ob.Caption)
					else:
						lbl = "Hidden Column ('%s')" % ob.Caption
				elif isNode:
					lbl = "TreeNode: ('%s')" % (ob.Caption)
				else:
					if hasattr(ob, "Name"):
						lbl = ob.Name
					else:
						lbl = ustr(ob.__class__)
		self.txtObj.Value = lbl
		self.PropSheet.select(obj)
		self.MethodList.clear()
		self._objPropSheet.select(obj)

		if ob is not None:
			# Get the events
			evts = ob.DesignerEvents
			# Get the dict of all events that have method code defined for them.
			obEvtCode = self.Controller.getCodeForObject(ob)
			codeEvents = nonCodeEvents = []
			if obEvtCode is not None:
				codeEvents = obEvtCode.keys()
				codeEvents.sort()
			nonCodeEvents = [ev for ev in evts
					if ev not in codeEvents]
			nonCodeEvents.sort()
			# Add the events with code first
			for evt in codeEvents:
				newItem = self.MethodList.append(evt)
				self.MethodList.setItemBackColor(newItem, "lightblue")

			for evt in nonCodeEvents:
				newItem = self.MethodList.append(evt)
				self.MethodList.setItemBackColor(newItem, "lightgrey")
		self.refresh()
		self.layout()


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


	def _getMethodList(self):
		return self._methodList

	def _setMethodList(self, val):
		self._methodList = val


	def _getMethodSheet(self):
		return self._methodSheet

	def _setMethodSheet(self, val):
		self._methodSheet = val


	def _getObjectPropertySheet(self):
		return self._objPropSheet

	def _setObjectPropertySheet(self, val):
		self._objPropSheet = val


	def _getPropSheet(self):
		return self._propSheet

	def _setPropSheet(self, val):
		self._propSheet = val


	def _getTree(self):
		return self._tree

	def _setTree(self, val):
		self._tree = val


	Controller = property(_getController, _setController, None,
			_("Object to which this one reports events  (object (varies))"))

	MethodList = property(_getMethodList, _setMethodList, None,
			_("""List control containing all available methods for the
			selected object  (dListControl)"""))

	MethodSheet = property(_getMethodSheet, _setMethodSheet, None,
			_("Reference to the panel containing the MethodList  (MethodSheet)"))

	ObjectPropertySheet = property(_getObjectPropertySheet,
			_setObjectPropertySheet, None, _("""Reference to the panel
			containing the ObjectPropertySheet  (ObjectPropertySheet)"""))

	Tree = property(_getTree, _setTree, None,
			_("Reference to the contained object tree  (TreeSheet)"))

	PropSheet = property(_getPropSheet, _setPropSheet, None,
			_("Reference to the contained prop sheet  (PropSheet)"))


