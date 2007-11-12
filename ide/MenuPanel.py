#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import dabo
dabo.ui.loadUI("wx")
from dabo.dLocalize import _
import dabo.dEvents as dEvents
from MenuDesignerComponents import CaptionPanel
from MenuDesignerComponents import CaptionBitmapPanel
from MenuDesignerComponents import SeparatorPanel



class MenuPanel(CaptionPanel):
	"""This class represents a menu."""
	def afterInit(self):
		# Name for the saved mnxml file
		self._className = "MenuPanel"
		# Displayed name
		self._commonName = "Menu"

		class _ItemPanel(dabo.ui.dPanel):
			_className = "MenuItemPanel"
			def __init__(self, *args, **kwargs):
				# Name for the saved mnxml file
				self._controller = None
				super(_ItemPanel, self).__init__(*args, **kwargs)
			
			def processContextMenu(self, obj, evt):
				self.Controller.processContextMenu(obj, evt)					
			
			def _getController(self):
				return self._controller
		
			def _setController(self, val):
				self._controller = val
		
			Controller = property(_getController, _setController, None,
					_("Object to which this panel is associated  (MenuPanel)"))

		# Add the panel that will hold the menu items. It needs to
		# be a child of the menu bar's parent, which would be this 
		# control's grandparent.
		gp = self.Parent.Parent
		localPos = (self.Left, self.Bottom)
		formPos = self.Parent.formCoordinates(localPos)
		self.itemList = lst = _ItemPanel(gp, Controller=self, Position=formPos,
				Visible=True)
		
		sz = lst.Sizer = dabo.ui.dSizer("V")
		sz.DefaultBorder = 1
		sz.DefaultBorderTop = True
		
		# Dict to hold additional item information
		self.itemDict = {}
		# Holds the active object during context menu actions
		self._contextObj = None
		
	
	def __del__(self):
		try:
			self.itemList.release()
		except: pass
		
		
	def layout(self):
		dabo.ui.callAfterInterval(100, self.itemList.layout, resetMin=True)
 		dabo.ui.callAfterInterval(100, self.itemList.fitToSizer)


	def append(self, caption, key=None, picture=None, help=None, 
			bindfunc=None, separator=False):
		return self.insert(None, caption, key=None, picture=picture, 
				help=help, bindfunc=bindfunc, separator=separator)
	
	
	def insert(self, pos, caption, key=None, picture=None, help=None, 
			bindfunc=None, separator=False):
		if pos is None:
			# Called from append
			pos = len(self.itemList.Children)
		if separator:
			itm = SeparatorPanel(self.itemList, Controller=self)
		else:
			itm = CaptionBitmapPanel(self.itemList, Caption=caption,
					Controller=self, Visible=self.Visible)
			itm._className = "MenuItemPanel"
			itm._commonName = "Menu Item"
			itm.isMenuItem = True
			# Add the item to the dict
			self.itemDict[itm] = {"caption": caption, "key": key, "picture": picture, 
					"bindfunc": bindfunc}
			if picture:
				itm.Picture = picture
		
		self.itemList.Height += itm.Height
		self.itemList.Sizer.insert(pos, itm, "x")
		self.layout()
		self.Controller.updateLayout()
		return itm
		
	
	def appendSeparator(self):
		ret = self.append("", separator=True)
		self.layout()
		self.Controller.updateLayout()
		return ret
	

	def insertSeparator(self, pos):
		ret = self.insert(pos, "", separator=True)
		self.layout()
		self.Controller.updateLayout()
		return ret
		
	
	def processContextMenu(self, obj, evt):
		self._contextObj = obj
		pop = dabo.ui.dMenu()
		if not isinstance(obj, SeparatorPanel):
			pop.append("Edit", OnHit=self.onEdit)
			pop.appendSeparator()
		pop.append("Add Item Above", OnHit=self.onAddAbove)
		pop.append("Add Item Below", OnHit=self.onAddBelow)
		pop.append("Add Separator Above", OnHit=self.onAddAbove)
		pop.append("Add Separator Below", OnHit=self.onAddBelow)
		if obj.getPositionInSizer() != 0:
			pop.append("Move Up", OnHit=self.onMoveUp)
		if obj.getPositionInSizer() != len(obj.ControllingSizer.Children)-1:
			pop.append("Move Down", OnHit=self.onMoveDown)
		pop.appendSeparator()
		pop.append("Delete", OnHit=self.onDelete)
		self.showContextMenu(pop)


	def onEdit(self, evt):
		obj = self._contextObj
		txt = self.capText = dabo.ui.dTextBox(obj.Parent, Value=obj.Caption,
				Position=obj.Position, Size=obj.Size)
		txt.bindEvent(dEvents.LostFocus, self.onEndEdit)
		txt.bindEvent(dEvents.KeyChar, self.onTextCapChar)
		obj.hide()
		txt.setFocus()
		
		
	def onTextCapChar(self, evt):
		if evt.keyCode == 13:
			self.onEndEdit(evt)
			
	
	def onEndEdit(self, evt):
		cap = self.capText.Value
		self.capText.release()
		if cap:
			self._contextObj.Caption = cap
		self._contextObj.show()
		self._contextObj = None
		self.layout()
		self.Controller.updateLayout()
		
		
	def onAddAbove(self, evt):
		pos = self._contextObj.getPositionInSizer()
		return self.addFromContextMenu(pos, evt)
	
	
	def onAddBelow(self, evt):
		pos = self._contextObj.getPositionInSizer() + 1
		return self.addFromContextMenu(pos, evt)
		
		
	def addFromContextMenu(self, pos, evt):
		obj = self._contextObj
		self._contextObj = None
		if "Separator" in evt.EventObject.Caption:
			return self.insertSeparator(pos)
		else:
			return self.addItem(pos)

	
	def addItem(self, pos):
		itm = None
		cap = dabo.ui.getString("Caption for new menu item?")
		if cap:
			itm = self.insert(pos, cap)
			self.Controller.select(itm)
		return itm
		
	
	def onMoveDown(self, evt):
		obj = self._contextObj
		pos = obj.getPositionInSizer()
		sz = obj.ControllingSizer
		sz.remove(obj)
		sz.insert(pos+1, obj, "x")
		sz.layout()
		self.Controller.updateLayout()
	
	
	def onMoveUp(self, evt):
		obj = self._contextObj
		pos = obj.getPositionInSizer()
		sz = obj.ControllingSizer
		sz.remove(obj)
		sz.insert(pos-1, obj, "x")
		sz.layout()
		self.Controller.updateLayout()
	
	
	def onDelete(self, evt):
		obj = self._contextObj
		if not obj:
			return
		obj.ControllingSizer.remove(obj)
		obj.release()
		self.layout()
		self.Controller.updateLayout()


	def onMouseLeftClick(self, evt):
		self.Parent.menuClick(self)
	
	
	def _getChildren(self):
		return self.itemList.Children


	def _getPanelVisible(self):
		return self.itemList.Visible

	def _setPanelVisible(self, val):
#		print "SETVIS", self.Caption, val
		if val:
			localPos = (self.Left, self.Bottom)
			formPos = self.Parent.formCoordinates(localPos)
			self.itemList.Position = formPos
			self.Controller.onShowPanel(self)
		self.itemList.Visible = val
		self.itemList.Parent.clear()
		self.layout()
		self.itemList.Parent.refresh()


	Children = property(_getChildren, None, None,
			_("Returns a list of menu items for this menu (read-only) (list)"))
	
	PanelVisible = property(_getPanelVisible, _setPanelVisible, None,
			_("Determines if the menu is currently 'open'  (bool)"))
	
		

