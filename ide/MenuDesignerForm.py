#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import dabo
dabo.ui.loadUI("wx")
from dabo.dLocalize import _
import dabo.dEvents as dEvents
import dabo.lib.xmltodict as xtd
from ClassDesignerExceptions import PropertyUpdateException
from MenuBarPanel import MenuBarPanel
from MenuPanel import MenuPanel
from MenuDesignerPropForm import MenuPropForm
from MenuDesignerComponents import CaptionBitmapPanel
from MenuDesignerComponents import SeparatorPanel



class MenuDesignerForm(dabo.ui.dForm):
	def __init__(self, *args, **kwargs):
		self._selection = None
		self._menuFile = None
		self._propForm = None
		self._propSheet = None
		super(MenuDesignerForm, self).__init__(*args, **kwargs)
		self.autoClearDrawings = True
		self.Caption = "Dabo Menu Designer"
		self.mainPanel = dabo.ui.dPanel(self)
		self.Sizer.append1x(self.mainPanel)
		sz = self.mainPanel.Sizer = dabo.ui.dSizer("v")
		self.previewButton = btn = dabo.ui.dButton(self.mainPanel, 
				Caption="Preview", OnHit=self.onPreview)
		sz.append(btn, border=10, halign="center")
		sz.append(dabo.ui.dLine(self.mainPanel), "x", border=10)
		self.menubar = MenuBarPanel(self.mainPanel)
		sz.append(self.menubar, border=30)
		self.menubar.Controller = self
		self.clear()
		self.layout()
	
	
	def onPreview(self, evt):
		class PreviewWindow(dabo.ui.dForm):
			def initProperties(self):
				self.Caption = "Menu Preview"
				self.ShowMenuBar = False
			def afterInit(self):
				mp = dabo.ui.dPanel(self)
				self.Sizer.append1x(mp)
				sz = mp.Sizer = dabo.ui.dSizer("v")
				sz.appendSpacer(30)
				self.lblResult = dabo.ui.dLabel(mp, Caption="Menu Selection: \n ", FontBold=True,
						ForeColor="darkred", AutoResize=True, Alignment="Center")
				self.lblResult.FontSize += 4
				sz.append(self.lblResult, halign="center", border=10)
				btn = dabo.ui.dButton(mp, Caption="Close Menu Preview",
						OnHit=self.onDeactivate)
				sz.append(btn, halign="center", border=30)
				mp.fitToSizer()
			def onDeactivate(self, evt):
				self.release()
			def notify(self, evt):
				itm = evt.EventObject
				cap = "Menu Selection: %s\n" % itm.Caption
				fncText = itm._bindingText
				if fncText:
					cap = "%sFunction: %s" % (cap, fncText)
				self.lblResult.Caption = cap
				self.layout()
				
		propDict = self.menubar.getDesignerDict()
		xml = xtd.dicttoxml(propDict)
		win = PreviewWindow(self, Centered=True)
		mb = dabo.ui.createMenuBar(xml, win, win.notify)
		win.MenuBar = mb
		win.show()
		
		
	def afterInitAll(self):
		self.PropSheet.Controller = self
		self.PropForm.show()
		self.Selection = None
		#dabo.ui.callAfterInterval(300, self.initialLayout)
		self.initialLayout()
	
	
	def initialLayout(self):
		print "INITLAY"
# 		self.menubar.clear()
# 		self.mainPanel.clear()
		self.menubar.quickMenu()
		self.layout()
		dabo.ui.callAfterInterval(500, self.foo)
	def foo(self):
		try:
			firstMenu = self.menubar.Menus[0]
# 			self.menubar.hideAllBut(firstMenu)
			self.Selection = firstMenu
			firstMenu.PanelVisible = True
		except IndexError:
			# No such menu
			pass
		
	
	def afterSetMenuBar(self):
		mbar = self.MenuBar
		fm = mbar.getMenu(_("File"))
		fm.append(_("Save"), HotKey="Ctrl+S", OnHit=self.onSave,
				help=_("Save the menu"))
	
	
	def getObjectHierarchy(self, parent=None, level=0):
		"""Returns a list of 2-tuples representing the structure of
		the objects on this form. The first element is the nesting level,
		and the second is the object. The objects are in the order
		created, irrespective of sizer position.
		"""
		if parent is None:
			parent = self.menubar
		ret = [(level, parent)]
		for kid in parent.Children:
			ret += self.getObjectHierarchy(kid, level+1)
		return ret
	
	
	def updateLayout(self):
		try:
			self.PropForm.updateLayout()
		except AttributeError:
			# Prop form not yet created
			pass
		
	
	def onSave(self, evt):
		self.saveMenu()
	
	
	def saveMenu(self):
		if not self._menuFile:
			self._menuFile = dabo.ui.getSaveAs(wildcard="mnxml")
			if not self._menuFile:
				# User canceled
				return
			else:
				if not os.path.splitext(self._menuFile)[1] == ".mnxml":
					self._menuFile += ".mnxml"
		
		propDict = self.menubar.getDesignerDict()
		xml = xtd.dicttoxml(propDict)
		open(self._menuFile, "wb").write(xml)


	def openClass(self, pth):
		if not os.path.exists(pth):
			dabo.ui.stop("The file '%s' does not exist" % pth)
			return
		xml = open(pth).read()
		try:
			dct = xtd.xmltodict(xml)
		except:
			raise IOError, _("This does not appear to be a valid class file.")
		
	
	def updatePropVal(self, prop, val, typ):
		obj = self.Selection
		if obj is None:
			return
		if typ is bool:
			val = bool(val)
		if isinstance(val, basestring):
			strVal = val
		else:
			strVal = unicode(val)
		if typ in (str, unicode) or ((typ is list) and isinstance(val, basestring)):
			# Escape any single quotes, and then enclose 
			# the value in single quotes
			strVal = "u'" + self.escapeQt(strVal) + "'"
		try:
			exec("obj.%s = %s" % (prop, strVal) )
		except StandardError, e:
			raise PropertyUpdateException, e
		self.PropForm.updatePropGrid()
		# This is necessary to force a redraw when some props change.
		self.select(obj)
		try:
			obj.setWidth()
		except AttributeError:
			pass
		self.layout()
					

	def onShowPanel(self, menu):
		"""Called when code makes a menu panel visible."""
		self.menubar.hideAllBut(menu)
		
		
	def select(self, obj):
		try: print "SELE", obj.Caption
		except: print "SELE NONE"
		if obj is self._selection:
			print "SAME"
			return
		self.lockDisplay()
		if self._selection is not None:
			print "UNSEL", self._selection.Caption
			self._selection.Selected = False
		self._selection = obj
		self.PropForm.select(obj)
		print "OBJ.SELECTED"
		obj.Selected = True
		try: print "ENSURE", obj.Caption
		except: print "eENSEURE NONE"

		self.ensureVisible(obj)
		dabo.ui.callAfterInterval(100, self._selectAfter)
	def _selectAfter(self):
		try: print "SELE AFT", self._selection.Caption
		except: print "SELE AFT NONE"
		self.refresh()
		self.unlockDisplay()


	def treeSelect(self):
		"""Called by the tree when a new selection has been made 
		by the user.
		"""
		dabo.ui.callAfter(self.afterTreeSelect)
		
		
	def afterTreeSelect(self):
		self.PropForm.Tree._inAppSelection = True
		try:
			selObj = self.PropForm.Tree.getSelection()
		except AttributeError:
			# The tree hasn't been instantiated yet
			return
		self.select(selObj)
		self.PropForm.Tree._inAppSelection = False
		
	
	def ensureVisible(self, obj):
		"""When selecting a menu item, make sure that its menu is open."""
		if isinstance(obj, (list, tuple)):
			obj = obj[-1]
		if isinstance(obj, (CaptionBitmapPanel, SeparatorPanel)):
			obj.Controller.PanelVisible = True
		elif isinstance(obj, MenuPanel):
			obj.PanelVisible = True
			
	
	def escapeQt(self, s):
		sl = "\\"
		qt = "\'"
		return s.replace(sl, sl+sl).replace(qt, sl+qt)


	def _getPropForm(self):
		noProp = self._propForm is None
		if not noProp:
			# Make sure it's still a live object
			try:
				junk = self._propForm.Visible
			except dabo.ui.deadObjectException:
				noProp = True
		if noProp:
			pf = self._propForm = MenuPropForm(self, Visible=False,
					Controller=self)
			pf.restoreSizeAndPosition()
			self.updateLayout()
			pf.Visible = True
		return self._propForm


	def _getPropSheet(self):
		if self._propSheet is None:
			self._propSheet = self.PropForm.PropSheet
		return self._propSheet
		
		
	def _getSelection(self):
		return self._selection

	def _setSelection(self, val):
		self.select(val)


	PropForm = property(_getPropForm, None, None,
			_("""Reference to the form that contains the PropSheet
			object (MenuPropForm)"""))
	
	PropSheet = property(_getPropSheet, None, None, 
			_("Reference to the Property Sheet (PropSheet)") )
	
	Selection = property(_getSelection, _setSelection, None,
			_("Currently selected item  (CaptionPanel)"))
	
