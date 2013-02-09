#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dabo
from dabo.dPref import dPref
if __name__ == "__main__":
	import dabo.ui
	dabo.ui.loadUI("wx")


# 'InspectorFormClass' is defined at the bottom

inspector_source = '''<?xml version="1.0" encoding="mac-roman" standalone="no"?>
<dForm Name="dForm" Caption="Dabo Object Inspector" SaveRestorePosition="False" Top="168" Height="761" Width="846" designerClass="DesForm" Left="537">
	<code>
		<addkids><![CDATA[
def addkids(self, obj, node):
	if self._showSizers:
		try:
			kid = obj.Sizer
		except AttributeError:
			kid = None
		if kid:
			snode = node.appendChild(self.sizer_repr(kid))
			snode.Object = kid
			snode.ForeColor = "blue"
			self.addkids(kid, snode)
			return
	try:
		kids = obj.ChildObjects
	except AttributeError:
		# Not a sizer
		try:
			kids = obj.Children
		except AttributeError:
			# Not a dabo obj
			return
	if isinstance(obj, dabo.ui.dFormMixin):
		if obj.ToolBar:
			kids.append(obj.ToolBar)
		if obj.StatusBar:
			kids.append(obj.StatusBar)
	for kid in kids:
		if self.exclude(kid):
			continue
		nodeColor = None
		if isinstance(kid, wx._controls.ScrollBar):
			continue
# 		if isinstance(obj, dabo.ui.dSizerMixin):
# 			kid = obj.getItem(kid)
		if isinstance(kid, dabo.ui.dSizerMixin):
			txt = self.sizer_repr(kid)
			nodeColor = "blue"
		else:
			try:
				txt = kid.Name
			except AttributeError:
				if isinstance(kid, wx.Size):
					txt = "Spacer %s" % kid
					nodeColor = "darkred"
				else:
					txt = "%s" % kid
		txt = "%s (%s)" % (txt, self.cls_repr(kid.__class__))
		knode = node.appendChild(txt)
		if nodeColor is not None:
			knode.ForeColor = nodeColor
		knode.Object = kid
		self.addkids(kid, knode)
]]>
		</addkids>
		<clearHighlight><![CDATA[
def clearHighlight(self):
	if not self:
		return
	current = time.time()
	for expiration in self._highlights.keys():
		if expiration > current:
			continue
		toClear = self._highlights.pop(expiration)
		frm = toClear["targetForm"]
		if toClear["type"] == "drawing":
			try:
				frm.removeDrawnObject(toClear["drawingToClear"])
			except ValueError:
				pass
#			frm.forceSizerOutline()
		else:
			sz = toClear["outlinedSizer"]
			frm.removeFromOutlinedSizers(sz)
			frm._alwaysDrawSizerOutlines = toClear["drawSetting"]
			sz.outlineStyle = toClear["outlineStyle"]
			sz.outlineWidth = toClear["outlineWidth"]
		frm.clear()
		frm.refresh()
		self.refresh()
]]>
		</clearHighlight>
		<onCollapseTree><![CDATA[
def onCollapseTree(self, evt):
	self.objectTree.collapseCurrentNode()
]]>
		</onCollapseTree>
		<afterInit><![CDATA[
def afterInit(self):
	self.BasePrefKey = "object_inspector"
	self.PreferenceManager = dPref(key=self.BasePrefKey)
	self._highlights = {}
]]>
		</afterInit>
		<_setShowSizers><![CDATA[
def _setShowSizers(self, val):
	self._showSizers = val
]]>
		</_setShowSizers>
		<importStatements><![CDATA[
import time
import wx
from dabo.dLocalize import _
from dabo.dPref import dPref
]]>
		</importStatements>
		<formatName><![CDATA[
def formatName(self, obj):
	if not obj:
		return "< -dead object- >"
	try:
		cap = obj.Caption
	except AttributeError:
		cap = ""
	try:
		cls = obj.BaseClass
	except AttributeError:
		cls = obj.__class__
	classString = "%s" % cls
	shortClass = classString.replace("'", "").replace(">", "").split(".")[-1]
	if cap:
		ret = "%s (\\"%s\\")" % (shortClass, cap)
	else:
		try:
			ret = "%s (%s)" % (obj.Name, shortClass)
		except AttributeError:
			ret = "%s (%s)" % (obj, cls)
	return ret
]]>
		</formatName>
		<onToggleSizers><![CDATA[
def onToggleSizers(self, evt):
	self._showSizers = not self._showSizers
	self.createObjectTree()
]]>
		</onToggleSizers>
		<showPropVals><![CDATA[
def showPropVals(self, obj):
	rows = []
	props = []
	try:
		props = obj.getPropertyList(onlyDabo=True)
	except AttributeError:
		for c in obj.__class__.__mro__:
			if c is dabo.lib.propertyHelperMixin.PropertyHelperMixin:
				# Don't list properties lower down (e.g., from wxPython):
				break
			for item in dir(c):
				if item[0].isupper():
					if item in c.__dict__:
						if type(c.__dict__[item]) == property:
							if props.count(item) == 0:
								props.append(item)
	if isinstance(obj, wx._core.Size):
		props = ["_controllingSizer", "_controllingSizerItem", "Spacing"]

	for prop in props:
		if prop == "ShowColumnLabels":
			# Avoid the deprecation warning
			continue
		try:
			val = getattr(obj, prop)
		except (AttributeError, TypeError, dabo.ui.assertionException):
			# write-only or otherwise unavailable
			continue
		if prop.startswith("Dynamic") and val is None:
			continue
		if val is None:
			val = self.Application.NoneDisplay
		elif isinstance(val, basestring):
			val = "'%s'" % val
		elif isinstance(val, dabo.dObject.dObject):
			try:
				val = "'%s'" % self.formatName(val)
			except StandardError, e:
				pass
		rows.append({"prop": prop, "val": val})
	ds = dabo.db.dDataSet(rows)
	self.infoGrid.DataSet = ds
]]>
		</showPropVals>
		<sizer_repr><![CDATA[
def sizer_repr(self, sz):
	"""Returns an informative representation for a sizer"""
	if isinstance(sz, dabo.ui.dGridSizer):
		ret = "dGridSizer (%s x %s)" % (sz.HighRow, sz.HighCol)
	elif isinstance(sz, dabo.ui.dBorderSizer):
		ret = "dBorderSizer (%s, '%s')" % (sz.Orientation, sz.Caption)
	else:
		ret = "dSizer (%s)" % sz.Orientation
	return ret
]]>
		</sizer_repr>
		<_getShowSizers><![CDATA[
def _getShowSizers(self):
	try:
		return self._showSizers
	except AttributeError:
		return None
]]>
		</_getShowSizers>
		<exclude><![CDATA[
def exclude(self, obj):
	isFloat = (isinstance(obj, dabo.ui.dDialog) and
		hasattr(obj, "Above") and hasattr(obj, "Owner"))
	return isFloat or (obj is self)
]]>
		</exclude>
		<_getHighlightInfo><![CDATA[
def _getHighlightInfo(self, obj, frm):
	pos = obj.ClientToScreen((0, 0))
	if self.Application.Platform == "Mac":
		pos = frm.ScreenToClient(pos)
		dc = wx.WindowDC(frm)
	else:
		dc = wx.ScreenDC()
	return pos, dc
]]>
		</_getHighlightInfo>
		<setSelectedObject><![CDATA[
def setSelectedObject(self, obj, silent=False):
	try:
		self.objectTree.showObject(obj, displayFail=False)
		self.objectTree.expandCurrentNode()
	except RuntimeError, e:
		if not silent:
			dabo.ui.stop(e, "Object Inspector")
]]>
		</setSelectedObject>
		<onFindObject><![CDATA[
def onFindObject(self, evt):
	self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
	self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.OnCaptureLost)
	self.CaptureMouse()
	self.finding = wx.BusyInfo("Click on any widget in the app...")
]]>
		</onFindObject>
		<OnCaptureLost><![CDATA[
def OnCaptureLost(self, evt):
	self.Unbind(wx.EVT_LEFT_DOWN)
	self.Unbind(wx.EVT_MOUSE_CAPTURE_LOST)
	del self.finding
]]>
		</OnCaptureLost>
		<afterInitAll><![CDATA[
def afterInitAll(self):
	objnote = "NOTE: The 'obj' variable refers to the object selected in the tree."
	intro = "%s\\n%s" % (dabo.ui.getSystemInfo(), objnote)
	self.shell = dabo.ui.dShell(self.shellPanel, showInterpIntro=False,
			introText=intro)
	self.shell.interp.locals['self'] = self
	sz = self.shellPanel.Sizer = dabo.ui.dBorderSizer(self.shellPanel, Caption="Interactive Interpreter")
	sz.append1x(self.shell)
	dabo.ui.callEvery(250, self.clearHighlight)

	tb = self.ToolBar = dabo.ui.dToolBar(self, ShowCaptions=True)
	self.refreshButton = self.appendToolBarButton(name="Refresh", pic="refresh_tree.png",
			toggle=False, tip=_("Re-create the object tree"),
			OnHit=self.onRefreshTree)
	self.findButton = self.appendToolBarButton(name="Find", pic="find_object.png",
			toggle=False, tip=_("Find an object in your app in the tree"),
			OnHit=self.onFindObject)
	self.showSizersButton = self.appendToolBarButton(name="Show Sizers", pic="show_sizers.png",
			toggle=True, tip=_("Show/Hide sizers in the object hierarchy"),
			OnHit=self.onToggleSizers)
	self.expandButton = self.appendToolBarButton(name="Expand", pic="expand_tree.png",
			toggle=False, tip=_("Expand this node and all nodes under it."),
			OnHit=self.onExpandTree)
	self.collapseButton = self.appendToolBarButton(name="Collapse", pic="collapse_tree.png",
			toggle=False, tip=_("Collapse this node and all nodes under it."),
			OnHit=self.onCollapseTree)
	self.highlightButton = self.appendToolBarButton(name="Highlight", pic="highlight_item.png",
			toggle=False, tip=_("Highlight the selected node in your app."),
			OnHit=self.onHighlightItem)
	self.layout()
]]>
		</afterInitAll>
		<onRefreshTree><![CDATA[
def onRefreshTree(self, evt):
	self.createObjectTree()
]]>
		</onRefreshTree>
		<onExpandTree><![CDATA[
def onExpandTree(self, evt):
	self.objectTree.expandCurrentNode()
]]>
		</onExpandTree>
		<cls_repr><![CDATA[
def cls_repr(self, cls):
	"""Returns a readable representation for a class"""
	txt = "%s" % cls
	prfx, clsname, suff = txt.split("'")
	return clsname
]]>
		</cls_repr>
		<OnLeftDown><![CDATA[
def OnLeftDown(self, evt):
	self.ReleaseMouse()
	wnd = wx.FindWindowAtPointer()
	if wnd is not None:
		self.objectTree.showObject(wnd)
	else:
		dabo.ui.beep()
	self.OnCaptureLost(evt)
]]>
		</OnLeftDown>
		<onHighlightItem><![CDATA[
def onHighlightItem(self, evt):
	obj = self.objectTree.Selection.Object
	try:
		frm = obj.Form
	except AttributeError:
		return
	# Remove the highlight after 3 seconds
	expires = time.time() + 3
	entry = self._highlights[expires] = {}
	entry["targetForm"] = frm

	if isinstance(obj, dabo.ui.dSizerMixin):
		entry["type"] = "sizer"
		frm.addToOutlinedSizers(obj)
		frm.refresh()
		entry["outlinedSizer"] = obj
		entry["drawSetting"] = frm._alwaysDrawSizerOutlines
		entry["outlineStyle"] = obj.outlineStyle
		obj.outlineStyle = "dot"
		entry["outlineWidth"] = obj.outlineWidth
		obj.outlineWidth = 4
		frm._alwaysDrawSizerOutlines = True
	else:
		if isinstance(obj, dabo.ui.dFormMixin):
			# Don't highlight the form; just bring it to the foreground
			del self._highlights[expires]
			obj.bringToFront()
			return
		x, y = obj.formCoordinates()
		entry["type"] = "drawing"
		# Make sure outline is visible
		xDraw = max(0, x-3)
		yDraw = max(0, y-3)
		wDraw = min(frm.Width-xDraw, obj.Width+6)
		hDraw = min(frm.Height-yDraw, obj.Height+6)
		entry["drawingToClear"] = frm.drawRectangle(xDraw, yDraw, wDraw, hDraw,
				penWidth=3, penColor="magenta")
]]>
		</onHighlightItem>
		<object_selected><![CDATA[
def object_selected(self, obj):
	self.shell.interp.locals['obj'] = obj
	self.shellPanel.Sizer.Caption = "'obj' is %s" % self.formatName(obj)
	self.showPropVals(obj)
]]>
		</object_selected>
		<createObjectTree><![CDATA[
def createObjectTree(self):
	tree = self.objectTree
	try:
		currObj = tree.Selection.Object
		currForm = currObj.Form
	except AttributeError:
		# Nothing selected yet
		currObj = currForm = None
	tree.clear()
	root = tree.setRootNode("Top Level Windows")
	for win in self.Application.uiForms:
		if self.exclude(win):
			continue
		winNode = root.appendChild(self.formatName(win))
		winNode.Object = win
		self.addkids(win, winNode)
	root.expand()
	if currObj:
		nd = tree.nodeForObject(currObj)
		if not nd:
			nd = tree.nodeForObject(currForm)
		nd.Selected = True
]]>
		</createObjectTree>
	</code>

	<properties>
		<ShowSizers>
			<comment>Determines if sizers are displayed in the object hierarchy</comment>
			<defaultValue>False</defaultValue>
			<deller>None</deller>
			<getter>_getShowSizers</getter>
			<propName>ShowSizers</propName>
			<defaultType>boolean</defaultType>
			<setter>_setShowSizers</setter>
		</ShowSizers>
	</properties>

	<dSizer SlotCount="1" designerClass="LayoutSizer" Orientation="Vertical">
		<dSplitter SashPosition="380" sizerInfo="{'VAlign': 'Middle'}" designerClass="controlMix" Split="True" Orientation="Horizontal">
			<dPanel Width="842" AlwaysResetSizer="True" designerClass="MixedSplitterPanel" Name="dPanel2" Height="378">
				<dSizer SlotCount="1" designerClass="LayoutSizer" Orientation="Vertical">
					<dSplitter SashPosition="322" sizerInfo="{'VAlign': 'Middle'}" designerClass="controlMix" Split="True" Orientation="Vertical">
						<dPanel Width="320" AlwaysResetSizer="True" designerClass="MixedSplitterPanel" Name="dPanel2" Height="374">
							<dSizer SlotCount="1" designerClass="LayoutSizer" Orientation="Vertical">
								<dTreeView RegID="objectTree" sizerInfo="{'VAlign': 'Middle'}" designerClass="controlMix">
									<code>
										<showObject><![CDATA[
def showObject(self, obj, displayFail=True):
	nd = self.nodeForObject(obj)
	if nd:
		nd.Selected = True
		self.showNode(nd)
	elif displayFail:
		dabo.ui.stop(_("Couldn't find object: %s") % obj)
	else:
		raise RuntimeError(_("Object '%s' not found") % obj)
]]>
										</showObject>
										<onTreeSelection><![CDATA[
def onTreeSelection(self, evt):
	dabo.ui.callAfter(self.Form.object_selected, self.Selection.Object)
]]>
										</onTreeSelection>
										<expandCurrentNode><![CDATA[
def expandCurrentNode(self):
	self.expandBranch(self.Selection)
]]>
										</expandCurrentNode>
										<collapseCurrentNode><![CDATA[
def collapseCurrentNode(self):
	self.collapseBranch(self.Selection)
]]>
										</collapseCurrentNode>
									</code>

									<dNode Caption="This is the root" designerClass="controlMix">
										<dNode Caption="First Child" designerClass="controlMix"></dNode>
										<dNode Caption="Second Child" designerClass="controlMix">
											<dNode Caption="Grandkid #1" designerClass="controlMix"></dNode>
											<dNode Caption="Grandkid #2" designerClass="controlMix">
												<dNode Caption="Great-Grandkid #1" designerClass="controlMix"></dNode>
											</dNode>
											<dNode Caption="Grandkid #3" designerClass="controlMix"></dNode>
										</dNode>
										<dNode Caption="Third Child" designerClass="controlMix"></dNode>
									</dNode>
								</dTreeView>
							</dSizer>
						</dPanel>
						<dPanel Width="511" AlwaysResetSizer="True" designerClass="MixedSplitterPanel" Name="dPanel1" Height="374">
							<dSizer SlotCount="1" designerClass="LayoutSizer" Orientation="Vertical">
								<dGrid ColumnCount="2" RegID="infoGrid" SelectionMode="Row" designerClass="controlMix" sizerInfo="{}">
									<code>
										<onGridMouseLeftClick><![CDATA[
def onGridMouseLeftClick(self, evt):
	def later():
		ds = self.DataSet
		row = ds[self.CurrentRow]
		prop = row["prop"]
		self.Form.PreferenceManager.excluded_props.setValue(prop, True)
		lds = list(ds)
		lds.remove(row)
		self.DataSet = dabo.db.dDataSet(lds)

	if evt.altDown:
		dabo.ui.callAfterInterval(250, later)
]]>
										</onGridMouseLeftClick>
									</code>

									<dColumn Width="169" Caption="Property" HorizontalAlignment="Right" DataField="prop" designerClass="controlMix" Order="0"></dColumn>
									<dColumn Caption="Value" DataField="val" designerClass="controlMix" Order="10" Width="399"></dColumn>
								</dGrid>
							</dSizer>
						</dPanel>
					</dSplitter>
				</dSizer>
			</dPanel>
			<dPanel Width="842" AlwaysResetSizer="True" designerClass="MixedSplitterPanel" Name="dPanel1" Height="332">
				<dSizer SlotCount="1" designerClass="LayoutSizer" Orientation="Vertical">
					<dPanel RegID="shellPanel" sizerInfo="{'VAlign': 'Middle'}" AlwaysResetSizer="True" designerClass="controlMix"></dPanel>
				</dSizer>
			</dPanel>
		</dSplitter>
	</dSizer>
</dForm>
'''

InspectorFormClass = dabo.ui.createClass(inspector_source)
