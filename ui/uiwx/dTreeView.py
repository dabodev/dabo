import dabo
import re, os, glob
import wx
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
import dabo.common.dColors as dColors


class dNode(dabo.common.dObject):
	"""Wrapper class for the tree nodes."""
	def __init__(self, tree, id, txt, parent):
		self.tree = tree
		# The 'id' in this case is a wxPython wx.TreeItemID object used
		# by wx to work with separate nodes.
		self.id = id
		self.txt = txt
		self.parent = parent
	
	
	def expand(self):
		self.tree.expand(self)
	
	
	def collapse(self):
		self.tree.collapse(self)
	
	
	def show(self):
		self.tree.showNode(self)
		
	
	def appendChild(self, txt):
		return self.tree.appendNode(self, txt)
	
	
	def removeChild(self, txt):
		"""Removes the child node whose text matches the passed value"""
		mtch = self.tree.find(txt)
		# We have a list of matching nodes. Find the first whose parent
		# is this object, and delete it
		for m in mtch:
			if m.parent == self:
				self.tree.removeNode(m)
				break
		return
		
	
	def _getBackColor(self):
		return self.tree.GetItemBackgroundColour(self.id)
	def _setBackColor(self, val):
		if type(val) in (unicode, str):
			try:
				val = dColors.colorTupleFromName(val)
			except: pass
		self.tree.SetItemBackgroundColour(self.id, val)
	
	def _getBold(self):
		return self.tree.IsBold(self.id)
	def _setBold(self, val):
		self.tree.SetItemBold(self.id, val)

	def _getForeColor(self):
		return self.tree.GetItemTextColour(self.id)
	def _setForeColor(self, val):
		if type(val) in (unicode, str):
			try:
				val = dColors.colorTupleFromName(val)
			except: pass
		self.tree.SetItemTextColour(self.id, val)
	
	def _getImg(self):
		return self.tree.getNodeImg(self)
	def _setImg(self, key):
		return self.tree.setNodeImg(self, key)
		
	def _getCap(self):
		return self.tree.GetItemText(self.id)
	def _setCap(self, val):
		self.tree.SetItemText(self.id, val)
	
	def _getChildren(self):
		return self.tree.getChildren(self)

	def _getDescendents(self):
		return self.tree.getDescendents(self)

	def _getSel(self):
		sel = self.tree.Selection
		if type(sel) == list:	
			ret = self in sel
		else:
			ret = (self == sel)
		return ret
	def _setSel(self, val):
		self.tree.SelectItem(self.id, val)

	def _getSiblings(self):
		return self.tree.getSiblings(self)

	
	BackColor = property(_getBackColor, _setBackColor, None,
			_("Background color of this node  (wx.Colour)") )
			
	Caption = property(_getCap, _setCap, None,
			_("Returns/sets the text of this node.  (str)") )
			
	Children = property(_getChildren, None, None,
			_("List of all nodes for which this is their parent node.  (list of dNodes)") )
	
	Descendents = property(_getDescendents, None, None,
			_("List of all nodes for which this node is a direct ancestor.  (list of dNodes)") )
	
	FontBold = property(_getBold, _setBold, None, 
			_("Bold status for the text of this node.  (bool)") )
		
	ForeColor = property(_getForeColor, _setForeColor, None,
			_("Foreground (text) color of this node  (wx.Colour)") )
			
	Image = property(_getImg, _setImg, None,
			_("""Sets the image that is displayed on the node. This is
			determined by the key value passed, which must refer to an 
			image already added to the parent tree. 	When used to retrieve 
			an image, it returns the index of the node's image in the parent 
			tree's image list.   (int)""") )
			
	Selected = property(_getSel, _setSel, None,
			_("Is this node selected?.  (bool)") )
	
	Siblings = property(_getSiblings, None, None,
			_("List of all nodes with the same parent node.  (list of dNodes)") )
	
	

class dTreeView(wx.TreeCtrl, dcm.dControlMixin):
	_IsContainer = False
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dTreeView
		self.nodes = []

		style = self.extractKey(kwargs, "style")
		if not style:
			style = wx.TR_DEFAULT_STYLE
		ed = self.extractKey(kwargs, "editable")
		if ed:
			style = style | wx.TR_EDIT_LABELS
		isMultiSel = self.extractKey(kwargs, "MultiSelect")
		self.__multiSelect = isMultiSel
		if isMultiSel:
			style = style | wx.TR_MULTIPLE | wx.TR_EXTENDED		

		preClass = wx.PreTreeCtrl
		dcm.dControlMixin.__init__(self, preClass, parent, properties, style=style, *args, **kwargs)
		# Dictionary for tracking images by key value
		self.__imageList = {}	
		
		self.bindEvent(dEvents.Hit, self.onHit)
		self.bindEvent(dEvents.TreeSelection, self.onSelection)
		self.bindEvent(dEvents.TreeItemCollapse, self.onItemCollapse)
		self.bindEvent(dEvents.TreeItemExpand, self.onItemExpand)

		
	def _initEvents(self):
		super(dTreeView, self)._initEvents()
		self.Bind(wx.EVT_LEFT_UP, self._onWxHit)
		self.Bind(wx.EVT_TREE_SEL_CHANGED, self._onTreeSel)
		self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self._onTreeItemCollapse)
		self.Bind(wx.EVT_TREE_ITEM_EXPANDED, self._onTreeItemExpand)

	
	def setRootNode(self, txt):
		id = self.AddRoot(txt)
		ret = dNode(self, id, txt, None)
		self.nodes.append(ret)
		return ret
	
	
	def appendNode(self, node, txt):
		id = self.AppendItem(node.id, txt)
		ret = dNode(self, id, txt, node)
		self.nodes.append(ret)
		return ret


	def removeNode(self, node):
		self.Delete(node.id)
		for n in node.Descendents:
			self.nodes.remove(n)
		self.nodes.remove(node)
	
	
	def expand(self, node):
		self.Expand(node.id)
	
	
	def collapse(self, node):
		self.Collapse(node.id)
	
	
	def expandAll(self):	
		for n in self.nodes:
			self.expand(n)
	
	
	def collapseAll(self):
		for n in self.nodes:
			self.collapse(n)
	
	
	def showNode(self, node):
		self.EnsureVisible(node.id)
		
		
	# Image-handling function
	def addImage(self, img, key=None):
		""" Adds the passed image to the control's ImageList, and maintains
		a reference to it that is retrievable via the key value.
		"""
		if key is None:
			key = str(img)
		if type(img) in (str, unicode):
			img = dabo.ui.dIcons.getIconBitmap(img)
		il = self.GetImageList()
		if not il:
			il = wx.ImageList(16, 16, initialCount=0)
			self.AssignImageList(il)
		idx = il.Add(img)
		self.__imageList[key] = idx
		
	
	def setNodeImg(self, node, imgKey):
		""" Sets the specified node's image to the image corresponding
		to the specified key. May also optionally pass the index of the 
		image in the ImageList rather than the key.
		"""
		if type(imgKey) == int:
			imgIdx = imgKey
		else:
			imgIdx = self.__imageList[imgKey]
		self.SetItemImage(node.id, imgIdx)

	
	def getNodeImg(self, node):
		""" Returns the index of the specified node's image in the 
		current image list, or -1 if no image is set for the node.
		"""
		ret = self.GetItemImage(node.id)
		return ret
		
	
	def getChildren(self, node):
		""" Returns a list of all nodes that are child nodes of this node."""
		ret = [n for n in self.nodes
				if n.parent == node]
		return ret
	
	
	def getDescendents(self, node):
		"""  Returns a list of all nodes that are direct descendents of this node. """
		ret = []
		for n in self.nodes:
			par = n.parent
			while par:
				if par == node:
					ret.append(n)
					break
				else:
					par = par.parent
		return ret


	def getSiblings(self, node):
		""" Returns a list of all nodes at the same level as the specified
		node. The specified node is included in the list.
		"""
		ret = [n for n in self.nodes
				if n.parent == node.parent]
		return ret
	

	def find(self, srch, top=None):
		""" Searches the nodes collection for all nodes that match
		whose text matches the passed search value (if a text value
		was passed). If a wxPython TreeItemID object is passed, returns
		a list nodes matching that id value. If a specific node is passed
		in the top property, the search is limited to descendents of that
		node.
		Returns a list of matching nodes.
		"""
		ret = []
		if top is None:
			nodes = self.nodes
		else:
			nodes = top.Descendents
		if type(srch) in (unicode, str):
			ret = [n for n in nodes 
				if n.txt == srch ]
		elif isinstance(srch, wx.TreeItemId):
			ret = [n for n in nodes 
				if n.id == srch ]
		return ret
		
		
	def findPattern(self, srchPat, top=None):
		""" Allows for regexp pattern matching in order to find matching
		nodes using less than exact matches. If a specific node is passed
		in the top property, the search is limited to descendents of that
		node.
		Returns a list of matching nodes.
		"""
		ret = []
		if top is None:
			nodes = self.nodes
		else:
			nodes = top.Descendents
		if type(srchPat) in (unicode, str):
			ret = [n for n in nodes 
				if re.match(srchPat, n.txt) ]
		return ret
	
	
	def makeDirTree(self, dirPath, wildcard=None, showHidden=False):
		self.DeleteAllItems()
		# Add any trailing slash character
		self._pathNode = {}
		# Define the function to be passed to os.path.walk
		def addNode(showHid, currDir, fNames):
			prnt, nm = os.path.split(currDir)
			if not showHid:
				if nm[:1] == ".":
					return
			try:
				nd = self._pathNode[currDir] = self._pathNode[prnt].appendChild(nm)
			except:
				# If this is the first entry, we need to set the root
				if len(self._pathNode.keys()) == 0:
					nd = self._pathNode[currDir] = self.setRootNode(nm)
				else:
					# parent wasn't added, because it was hidden
					return
			for f in fNames:
				fullName = os.path.join(currDir, f)
				if os.path.isdir(fullName):
					# it will be added as a directory
					continue
				if not showHid:
					if f[:1] == ".":
						continue
				if wildcard is not None:
					res = glob.glob(os.path.join(currDir, wildcard))
					if not fullName in res:
						continue
				nd.appendChild(f)
		def sortNode(arg, currDir, fNames):
			self.SortChildren(self._pathNode[currDir].id)
		os.path.walk(dirPath, addNode, showHidden)
		os.path.walk(dirPath, sortNode, None)


	# Event-handling code
	def _onTreeSel(self, evt):
		self.raiseEvent(dEvents.TreeSelection, evt)
	def _onTreeItemCollapse(self, evt):
		self.raiseEvent(dEvents.TreeItemCollapse, evt)
	def _onTreeItemExpand(self, evt):
		self.raiseEvent(dEvents.TreeItemExpand, evt)
	def onSelection(self, evt): pass
	def onHit(self, evt): pass
	def onItemCollapse(self, evt): pass
	def onItemExpand(self, evt): pass


	def addDummyData(self):
		""" For testing purposes! """
		self.DeleteAllItems()
		r = self.setRootNode("This is the root")
		c1 = r.appendChild("First Child")
		c2 = r.appendChild("Second Child")
		c3 = r.appendChild("Third Child")
		c21 = c2.appendChild("Grandkid #1")
		c22 = c2.appendChild("Grandkid #2")
		c23 = c2.appendChild("Grandkid #3")
		c221 = c22.appendChild("Great-Grandkid #1")
		
	
	def _getSelection(self):
		if self.__multiSelect:
			ids = self.GetSelections()
			ret = [ n for n in self.nodes
					if n.id in ids]
		else:
			id = self.GetSelection()
			ret = [ n for n in self.nodes
					if n.id == id][0]
		return ret
	def _setSelection(self, node):
		if self._constructed():
			self.SelectItem(node.id)
		else:
			self._properties["Selection"] = node
	
	
	Selection = property(_getSelection, _setSelection, None,
			_("""If this is not a MultiSelect tree, it returns the currently 
			selected node. If this is defined as MultiSelect, it will return
			a list of selected nodes.  (dNode or list of dNodes)""") )
		
			
if __name__ == "__main__":
	import test
	
	class TestTree(dTreeView):
		def afterInit(self): 
			self.addDummyData()
# 		self.Size = (300,400)
# 		self.expandAll()
# 		self.addImage("edit")
# 		self.addImage("browse")
# 		self.addImage("checkMark")

		def onSelection(self, evt):
			print "Selected node caption:", evt.EventData["selectedCaption"]
		def onItemCollapse(self, evt):
			print "Collapsed node caption:", evt.EventData["selectedCaption"]
		def onItemExpand(self, evt):
			print "Expanded node caption:", evt.EventData["selectedCaption"]
		
	test.Test().runTest(TestTree)
