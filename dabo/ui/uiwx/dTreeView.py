# -*- coding: utf-8 -*-
import re
import os
import glob
import wx
import dabo
from dabo.ui import makeDynamicProperty
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.lib.utils import ustr
import dabo.dColors as dColors
from dabo.dObject import dObject


class dNode(dObject):
	"""Wrapper class for the tree nodes."""
	def __init__(self, tree, itemID, parent):
		self._baseClass = dNode
		self.tree = tree
		# The 'itemID' in this case is a wxPython wx.TreeItemID object used
		# by wx to work with separate nodes.
		self.itemID = itemID
		self.parent = parent
		# Nodes can have objects associated with them
		self._object = None
		# Nodes can also be associated with a file path
		self._filePath = None
		# Custom text to display as a tooltip
		self._toolTipText = None
		# Add minimal Dabo functionality
		self.afterInit()

	def afterInit(self): pass


	def expand(self):
		self.tree.expand(self)


	def collapse(self):
		self.tree.collapse(self)


	def show(self):
		self.tree.showNode(self)


	def release(self):
		self.tree.removeNode(self)


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


	def _onFontPropsChanged(self, evt):
		# Sent by the dFont object when any props changed. Wx needs to be notified:
		self.tree.SetItemFont(self.itemID, self.Font._nativeFont)


	def _constructed(self):
		# For compatibility with mixin props.
		return True


	# Property definition code begins here
	def _getBackColor(self):
		return self.tree.GetItemBackgroundColour(self.itemID).Get()

	def _setBackColor(self, val):
		if isinstance(val, basestring):
			val = dColors.colorTupleFromName(val)
		self.tree.SetItemBackgroundColour(self.itemID, val)


	def _getCap(self):
		try:
			ret = self.tree.GetItemText(self.itemID)
		except dabo.ui.assertionException:
			ret = ""
		return ret

	def _setCap(self, val):
		self.tree.SetItemText(self.itemID, val)


	def _getChildren(self):
		return self.tree.getChildren(self)


	def _getDescendents(self):
		return self.tree.getDescendents(self)


	def _getExpanded(self):
		return self.tree.IsExpanded(self.itemID)

	def _setExpanded(self, val):
		try:
			if val:
				self.tree.expand(self)
			else:
				self.tree.collapse(self)
		except wx._core.PyAssertionError:
			# Happens when expandAll() is called and the root node is hidden
			# especially from dTreeView.refreshDisplay()
			pass


	def _getFont(self):
		if hasattr(self, "_font"):
			v = self._font
		else:
			v = self.Font = dabo.ui.dFont(_nativeFont=self.tree.GetItemFont(self.itemID))
		return v

	def _setFont(self, val):
		assert isinstance(val, dabo.ui.dFont)
		self._font = val
		if not self.IsRootNode or self.tree.ShowRootNode:
			# On some platforms exception is raised while operation
			# on hidden root node.
			self.tree.SetItemFont(self.itemID, val._nativeFont)
			val.bindEvent(dEvents.FontPropertiesChanged, self._onFontPropsChanged)
			dabo.ui.callAfterInterval(100, self.tree.refreshDisplay)


	def _getFontBold(self):
		try:
			return self.Font.Bold
		except AttributeError:
			return False

	def _setFontBold(self, val):
		self.Font.Bold = val
		dabo.ui.callAfterInterval(100, self.tree.refreshDisplay)


	def _getFontDescription(self):
		try:
			return self.Font.Description
		except AttributeError:
			return ""


	def _getFontInfo(self):
		try:
			return self.Font._nativeFont.GetNativeFontInfoDesc()
		except AttributeError:
			return ""


	def _getFontItalic(self):
		try:
			return self.Font.Italic
		except AttributeError:
			return False

	def _setFontItalic(self, val):
		self.Font.Italic = val
		dabo.ui.callAfterInterval(100, self.tree.refreshDisplay)


	def _getFontFace(self):
		try:
			return self.Font.Face
		except AttributeError:
			return ""

	def _setFontFace(self, val):
		self.Font.Face = val
		dabo.ui.callAfterInterval(100, self.tree.refreshDisplay)


	def _getFontSize(self):
		try:
			return self.Font.Size
		except AttributeError:
			return 10

	def _setFontSize(self, val):
		self.Font.Size = val
		dabo.ui.callAfterInterval(100, self.tree.refreshDisplay)


	def _getFontUnderline(self):
		try:
			return self.Font.Underline
		except AttributeError:
			return False

	def _setFontUnderline(self, val):
		self.Font.Underline = val
		dabo.ui.callAfterInterval(100, self.tree.refreshDisplay)


	def _getForeColor(self):
		return self.tree.GetItemTextColour(self.itemID).Get()

	def _setForeColor(self, val):
		if isinstance(val, basestring):
			val = dColors.colorTupleFromName(val)
		self.tree.SetItemTextColour(self.itemID, val)


	def _getFullCaption(self):
		ret = self.Caption
		if self.parent:
			ret = "%s.%s" % (self.parent._getFullCaption(), ret)
		return ret


	def _getImg(self):
		return self.tree.getNodeImg(self)

	def _setImg(self, key):
		return self.tree.setNodeImg(self, key)
		dabo.ui.callAfterInterval(100, self.tree.refreshDisplay)


	def _getIsRootNode(self):
		try:
			ret = self._isRootNode
		except AttributeError:
			ret = self._isRootNode = (self.tree.GetRootItem() == self.itemID)
		return ret


	def _getObject(self):
		return self._object

	def _setObject(self, val):
		if self._constructed():
			self._object = val
		else:
			self._properties["Object"] = val


	def _getSel(self):
		sel = self.tree.Selection
		if isinstance(sel, list):
			ret = self in sel
		else:
			ret = (self == sel)
		return ret

	def _setSel(self, val):
		self.tree.SelectItem(self.itemID, val)


	def _getSiblings(self):
		return self.tree.getSiblings(self)


	def _getToolTipText(self):
		return self._toolTipText

	def _setToolTipText(self, val):
		if self._constructed():
			self._toolTipText = val
		else:
			self._properties["ToolTipText"] = val


	BackColor = property(_getBackColor, _setBackColor, None,
			_("Background color of this node  (str, 3-tuple, or wx.Colour)") )

	Caption = property(_getCap, _setCap, None,
			_("Returns/sets the text of this node.  (str)") )

	Children = property(_getChildren, None, None,
			_("List of all nodes for which this is their parent node.  (list of dNodes)") )

	Descendents = property(_getDescendents, None, None,
			_("List of all nodes for which this node is a direct ancestor.  (list of dNodes)") )

	Expanded = property(_getExpanded, _setExpanded, None,
			_("Represents whether the node is Expanded (True) or collapsed.  (bool)"))

	Font = property(_getFont, _setFont, None,
			_("The font properties of the node. (obj)") )

	FontBold = property(_getFontBold, _setFontBold, None,
			_("Specifies if the node font is bold-faced. (bool)") )

	FontDescription = property(_getFontDescription, None, None,
			_("Human-readable description of the node's font settings. (str)") )

	FontFace = property(_getFontFace, _setFontFace, None,
			_("Specifies the font face for the node. (str)") )

	FontInfo = property(_getFontInfo, None, None,
			_("Specifies the platform-native font info string for the node. Read-only. (str)") )

	FontItalic = property(_getFontItalic, _setFontItalic, None,
			_("Specifies whether the node's font is italicized. (bool)") )

	FontSize = property(_getFontSize, _setFontSize, None,
			_("Specifies the point size of the node's font. (int)") )

	FontUnderline = property(_getFontUnderline, _setFontUnderline, None,
			_("Specifies whether node text is underlined. (bool)") )

	ForeColor = property(_getForeColor, _setForeColor, None,
			_("Foreground (text) color of this node  (str, 3-tuple, or wx.Colour)") )

	FullCaption = property(_getFullCaption, None, None,
			_("Full dot-separated string of the captions of this node and its ancestors (read-only) (str)"))

	Image = property(_getImg, _setImg, None,
			_("""Sets the image that is displayed on the node. This is
			determined by the key value passed, which must refer to an
			image already added to the parent tree. 	When used to retrieve
			an image, it returns the index of the node's image in the parent
			tree's image list.   (int)""") )

	IsRootNode = property(_getIsRootNode, None, None,
			_("Returns True if this is the root node (read-only) (bool)"))

	Object = property(_getObject, _setObject, None,
			_("Optional object associated with this node. Default=None  (object)"))

	Selected = property(_getSel, _setSel, None,
			_("Is this node selected?.  (bool)") )

	Siblings = property(_getSiblings, None, None,
			_("List of all nodes with the same parent node.  (list of dNodes)") )

	ToolTipText = property(_getToolTipText, _setToolTipText, None,
			_("""Text to display when the mouse hovers over this node. The tree's
			UseNodeToolTips property must be True for this to have any effect.  (str)"""))



	DynamicBackColor = makeDynamicProperty(BackColor)
	DynamicCaption = makeDynamicProperty(Caption)
	DynamicFont = makeDynamicProperty(Font)
	DynamicFontBold = makeDynamicProperty(FontBold)
	DynamicFontFace = makeDynamicProperty(FontFace)
	DynamicFontItalic = makeDynamicProperty(FontItalic)
	DynamicFontSize = makeDynamicProperty(FontSize)
	DynamicFontUnderline = makeDynamicProperty(FontUnderline)
	DynamicForeColor = makeDynamicProperty(ForeColor)
	DynamicImage = makeDynamicProperty(Image)
	DynamicSelected = makeDynamicProperty(Selected)
	DynamicToolTipText = makeDynamicProperty(ToolTipText)



class dTreeView(dcm.dControlMixin, wx.TreeCtrl):
	"""Creates a treeview, which allows display of hierarchical data."""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dTreeView

		# Dictionary for tracking images by key value
		self.__imageList = {}
		self.nodes = []
		self._rootNode = None
		# Class to use for creating nodes
		self._nodeClass = dNode
		# Default size for images added to the tree.
		self._imageSize = (16, 16)
		# Do we set tooltips from the nodes?
		self._useNodeToolTips = False
		# Store the default ToolTipText while UseNodeToolTips is True
		self._storedToolTipText = None

		style = self._extractKey((properties, attProperties, kwargs), "style", 0) | wx.TR_HAS_VARIABLE_ROW_HEIGHT
		# Default to showing buttons
		val = self._extractKey(attProperties, "ShowButtons", None)
		if val is not None:
			val = (val == "True")
		else:
			val = self._extractKey((properties, kwargs), "ShowButtons", True)
		if val:
			style = style | wx.TR_HAS_BUTTONS

		# Default to showing lines
		val = self._extractKey(attProperties, "ShowLines", None)
		if val is not None:
			val = (val == "True")
		else:
			val = self._extractKey((properties, kwargs), "ShowLines", True)
		if not val:
			style = style | wx.TR_NO_LINES

		# Default to showing root node
		val = self._extractKey(attProperties, "ShowRootNode", None)
		if val is not None:
			val = (val == "True")
		else:
			val = self._extractKey((properties, kwargs), "ShowRootNode", True)
		if not val:
			style = style | wx.TR_HIDE_ROOT

		# Default to showing root node lines
		val = self._extractKey(attProperties, "ShowRootNodeLines", None)
		if val is not None:
			val = (val == "True")
		else:
			val = self._extractKey((properties, kwargs), "ShowRootNodeLines", True)
		if val:
			style = style | wx.TR_LINES_AT_ROOT

		preClass = wx.PreTreeCtrl
		dcm.dControlMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, style=style, *args, **kwargs)


	def _initEvents(self):
		super(dTreeView, self)._initEvents()
		self.Bind(wx.EVT_LEFT_UP, self._onWxHit)
		self.Bind(wx.EVT_KEY_UP, self.__onKeyUp)
		self.Bind(wx.EVT_TREE_SEL_CHANGED, self.__onTreeSel)
		self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.__onTreeItemCollapse)
		self.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.__onTreeItemExpand)
		self.Bind(wx.EVT_TREE_ITEM_MENU, self.__onTreeItemContextMenu)
		self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.__onTreeBeginDrag)
		self.Bind(wx.EVT_TREE_END_DRAG, self.__onTreeEndDrag)
		self.Bind(wx.EVT_MOTION, self.__onTreeMouseMove)


	def __onTreeItemContextMenu(self, evt):
		self.raiseEvent(dEvents.TreeItemContextMenu, evt)


	def __onTreeBeginDrag(self, evt):
		if self._allowDrag(evt):
			evt.Allow()
		# We need to select the item being dragged
		# so we don't try to drag an old selected item
		self.SelectItem(evt.GetItem())
		evt.Skip()
		self.raiseEvent(dEvents.TreeBeginDrag, evt)


	def __onTreeEndDrag(self, evt):
		evt.Skip()
		# We need to select only our destination node
		if self.MultipleSelect:
			self.UnselectAll()
		self.SelectItem(evt.GetItem())
		self.raiseEvent(dEvents.TreeEndDrag, evt)


	def _allowDrag(self, evt):
		nd = self.find(evt.GetItem())
		return self.allowDrag(nd)


	def allowDrag(self, node):
		# Override in subclasses in needed.
		return True


	def _getInitPropertiesList(self):
		original = list(super(dTreeView, self)._getInitPropertiesList())
		original.remove("MultipleSelect")
		return tuple(original)


	def clear(self, clearImageList=False):
		self.DeleteAllItems()
		self.nodes = []
		if clearImageList:
			il = self.GetImageList()
			if il:
				il.RemoveAll()
			self.__imageList = {}


	def refreshDisplay(self):
		"""
		Changing some node appearance properties requires that the tree be
		collapsed and re-opened in order to update any sizing issues.
		"""
		self.lockDisplay()
		sel = self.Selection
		ndExp = ((nd, nd.Expanded) for nd in self.nodes
				if ((not nd.IsRootNode) or self.ShowRootNode))
		self.collapseAll()
		for nd, exp in ndExp:
			nd.Expanded = exp
		self.Selection = sel
		self.unlockDisplay()


	def getRootNode(self):
		return self._rootNode


	def setRootNode(self, txt):
		itemID = self.AddRoot(txt)
		ret = self._rootNode = self.NodeClass(self, itemID, None)
		if self.ShowRootNode:
			self.SetItemFont(ret.itemID, self.GetFont())
		self.nodes.append(ret)
		return ret


	def appendNode(self, node, txt):
		if node is None:
			# Get the root node
			ndid = self.GetRootItem()
		else:
			ndid = node.itemID
		itemID = self.AppendItem(ndid, txt)
		ret = self.NodeClass(self, itemID, node)
		self.SetItemFont(ret.itemID, self.GetFont())
		self.nodes.append(ret)
		return ret


	def removeNode(self, node):
		self.Delete(node.itemID)
		for n in node.Descendents:
			self.nodes.remove(n)
		self.nodes.remove(node)


	def expand(self, node):
		self.Expand(node.itemID)


	def collapse(self, node):
		self.Collapse(node.itemID)


	def expandAll(self):
		nds = self.nodes
		if not self.ShowRootNode:
			nds = [nd for nd in self.nodes
					if not nd.IsRootNode]
		for n in nds:
			self.expand(n)


	def collapseAll(self):
		nds = self.nodes
		if not self.ShowRootNode:
			nds = [nd for nd in self.nodes
					if not nd.IsRootNode]
		for n in nds:
			self.collapse(n)


	def expandBranch(self, nd):
		"""Expands the specified node, as well as any of its child nodes."""
		self.ExpandAllChildren(nd.itemID)


	def collapseBranch(self, nd):
		"""Collapses the specified node, as well as any of its child nodes."""
		self.CollapseAllChildren(nd.itemID)


	def showNode(self, node):
		self.EnsureVisible(node.itemID)


	# Image-handling function
	def addImage(self, img, key=None):
		"""
		Adds the passed image to the control's ImageList, and maintains
		a reference to it that is retrievable via the key value.
		"""
		# Default image size
		wd, ht = self.ImageSize
		il = self.GetImageList()
		if not il:
			il = wx.ImageList(wd, ht, initialCount=0)
			self.AssignImageList(il)
		else:
			if il.GetImageCount():
				wd, ht = il.GetSize(0)
		if key is None:
			key = ustr(img)
		if isinstance(img, basestring):
			img = dabo.ui.strToBmp(img, width=wd, height=ht)
		idx = il.Add(img)
		self.__imageList[key] = idx


	def setNodeImg(self, node, imgKey, which="normal"):
		"""
		Sets the specified node's image to the image corresponding to the
		specified key. May also optionally pass the index of the image in the
		image list rather than the key, which is the state of the node.

		Valid states are:

			'normal'
			'expanded'
			'selected'
			'selectedexpanded'

		"""
		whichdict = {"normal": wx.TreeItemIcon_Normal,
			"expanded": wx.TreeItemIcon_Expanded,
			"selected": wx.TreeItemIcon_Selected,
			"selectedexpanded": wx.TreeItemIcon_SelectedExpanded}
		if which.lower() not in whichdict:
			raise ValueError(_("Invalid Node State: %s") % which)
		if isinstance(imgKey, int):
			imgIdx = imgKey
		else:
			imgIdx = self.__imageList[imgKey]
		self.SetItemImage(node.itemID, imgIdx, whichdict[which.lower()])


	def getNodeImg(self, node, which="normal"):
		"""
		Returns the index of the specified node's image in the
		current image list, or -1 if no image is set for the node.
		Which is the state of the node.

		Valid states are:

			'normal'
			'expanded'
			'selected'
			'selectedexpanded'

		"""
		whichdict = {"normal": wx.TreeItemIcon_Normal,
			"expanded": wx.TreeItemIcon_Expanded,
			"selected": wx.TreeItemIcon_Selected,
			"selectedexpanded": wx.TreeItemIcon_SelectedExpanded}
		if which.lower() not in whichdict:
			raise ValueError(_("Invalid Node State: %s") % which)
		return self.GetItemImage(node.itemID, whichdict[which.lower()])


	def nodeForObject(self, obj):
		"""Given an object, returns the corresponding node."""
		try:
			return [nd for nd in self.nodes	if nd._object is obj][0]
		except IndexError:
			return None


	def getParentNode(self, node):
		"""
		Returns the node that is the parent of the given node, or
		None if the node is the root.
		"""
		parentID = self.GetItemParent(node.itemID)
		ret = self.find(parentID)
		if ret:
			if isinstance(ret, list):
				ret = ret[0]
		else:
			ret = None
		return ret


	def getChildren(self, node):
		"""Returns a list of all nodes that are child nodes of this node."""
		ret = [n for n in self.nodes
				if n.parent == node]
		return ret


	def getDescendents(self, node):
		"""Returns a list of all nodes that are direct descendents of this node."""
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
		"""
		Returns a list of all nodes at the same level as the specified
		node. The specified node is included in the list.
		"""
		ret = [n for n in self.nodes
				if n.parent == node.parent]
		return ret


	def find(self, srch, top=None):
		"""
		Searches the nodes collection for all nodes that match
		whose text matches the passed search value (if a text value
		was passed). If a wxPython TreeItemID object is passed, returns
		a list nodes matching that itemID value. If a specific node is passed
		in the top property, the search is limited to descendents of that
		node.
		Returns a list of matching nodes.
		"""
		ret = []
		if top is None:
			nodes = self.nodes
		else:
			nodes = top.Descendents
		if isinstance(srch, basestring):
			ret = [n for n in nodes
				if n.Caption == srch ]
		elif isinstance(srch, wx.TreeItemId):
			ret = [n for n in nodes
				if n.itemID == srch ]
		return ret


	def findPattern(self, srchPat, top=None):
		"""
		Allows for regexp pattern matching in order to find matching
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
		if isinstance(srchPat, basestring):
			ret = [n for n in nodes
				if re.match(srchPat, n.Caption) ]
		return ret


	# These related functions all use self._getRelative().
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	def nextSibling(self, nd=None):
		"""Returns the next sibling node, or None if there are no more"""
		return self._getRelative(nd, self.GetNextSibling)


	def priorSibling(self, nd=None):
		"""Returns the prior sibling node, or None if there are no more"""
		return self._getRelative(nd, self.GetPrevSibling)


	def nextNode(self, nd=None):
		"""
		If the current node has children, returns the first child node. If
		it has no children, returns the next sibling. If there are no next
		siblings, returns the next sibling of the parent node. If the parent
		node has no more siblings, returns the next sibling of the grand-
		parent node, etc. Returns None if we are at the absolute bottom
		of the flattened tree structure. Sometimes referred to as 'flatdown'
		navigation.
		"""
		if not isinstance(nd, dNode):
			nd = self.nodeForObject(nd)
		if nd is None:
			nd = self.Selection
			if isinstance(nd, list):
				if nd:
					nd = nd[0]
				else:
					# Empty list
					return None
		try:
			ret = self.getChildren(nd)[0]
		except IndexError:
			ret = None
		if ret is None:
			ret = self._getRelative(nd, self.GetNextSibling)
			while ret is None:
				# No more siblings. Go up the tree, getting the next
				# sibling of each parent until we either find one, or
				# we reach the top.
				nd = self.getParentNode(nd)
				if nd is None:
					break
				ret = self._getRelative(nd, self.GetNextSibling)
		return ret


	def priorNode(self, nd=None):
		"""
		Returns last child of the prior sibling node. If there
		are no prior siblings, returns the parent. Sometimes
		referred to as 'flatup' navigation.
		"""
		if not isinstance(nd, dNode):
			nd = self.nodeForObject(nd)
		if nd is None:
			nd = self.Selection
			if isinstance(nd, list):
				if nd:
					nd = nd[0]
				else:
					# Empty list
					return None
		ret = self._getRelative(nd, self.GetPrevSibling)
		if ret is None:
			try:
				ret = self.getParentNode(nd)
			except wx.PyAssertionError:
				pass
		else:
			# Find the last child of the last child of the last child...
			nd = ret
			kids = self.getChildren(nd)
			while kids:
				nd = kids[-1]
				kids = self.getChildren(nd)
			ret = nd
		return ret


	def _getRelative(self, nd, func):
		"""
		Used by nextNode(), nextSibling(), priorNode() and
		priorSibling() methods for relative movement.
		"""
		if nd is None:
			nd = self.Selection
		if isinstance(nd, list):
			if nd:
				nd = nd[0]
			else:
				# Empty list
				return None
		try:
			itemID = func(nd.itemID)
			ret = [nod for nod in self.nodes
					if nod.itemID == itemID][0]
		except IndexError:
			ret = None
		return ret
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


	def makeDirTree(self, dirPath, wildcard=None, ignored=None,
			showHidden=False, expand=False):
		"""
		Make this dTreeView show a filesystem directory hierarchy. You
		can specify a wildcard pattern: e.g., "\*py" will only include files
		ending in 'py'. You can also pass a list of wildcards, and files
		matching any of these will be included in the tree. If no wildcard
		is specified, all files will be included.

		You can also specify file patterns to ignore in the 'ignored' parameter.
		This can be a single string of a file pattern, or a list of such patterns.
		Any file matching any of these patterns will not be included in the tree.

		By default, hidden files (i.e., those beginning with a period) are ignored.
		You can optionally show them by passing True in the showHidden
		parameter.

		The tree defaults to fully collapsed; you can change it to fully
		expanded by passing True in the 'expand' parameter.

		Warning: Don't use this for huge hierarchies, as it blocks while
		filling the complete tree, instead of only filling the nodes as
		they are opened.
		"""
		self.clear(clearImageList=True)
		# Add the standard images for a directory tree
		self.addImage("folder", "folder")
		self.addImage("folderopen", "folderopen")
		self.addImage("normalfile", "file")
		self.addImage("executablefile", "executablefile")

		# Add any trailing slash character
		self._pathNode = {}
		# Define the function to be passed to os.path.walk
		def addNode(arg, currDir, fNames):
			wildcards, ignored, showHid = arg
			prnt, nm = os.path.split(currDir)
			if not showHid and nm.startswith("."):
				return
			try:
				nd = self._pathNode[currDir] = self._pathNode[prnt].appendChild(nm)
			except (KeyError, AttributeError):
				# If this is the first entry, we need to set the root
				if not self._pathNode:
					nd = self._pathNode[currDir] = self.setRootNode(nm)
				else:
					# parent wasn't added, because it was hidden
					return
			self.setNodeImg(nd, "folder", "normal")
			self.setNodeImg(nd, "folderopen", "expanded")
			nd.ToolTipText = nd._filePath = currDir
			acceptedNames = ignoredNames = None
			if wildcards is not None:
				acceptedNames = []
				for wc in wildcards:
					acceptedNames += glob.glob(os.path.join(currDir, wc.lower()))
					acceptedNames += glob.glob(os.path.join(currDir, wc.upper()))
			if ignored is not None:
				ignoredNames = []
				for ig in ignored:
					ignoredNames += glob.glob(os.path.join(currDir, ig.lower()))
					ignoredNames += glob.glob(os.path.join(currDir, ig.upper()))
			for f in fNames:
				fullName = os.path.join(currDir, f)
				if os.path.isdir(fullName):
					# it will be added as a directory
					continue
				if not showHid and f.startswith("."):
					continue
				if acceptedNames is not None:
					if fullName not in acceptedNames:
						continue
				if ignoredNames is not None:
					if fullName in ignoredNames:
						continue
				kid = nd.appendChild(f)
				kid._filePath = fullName
				self.setNodeImg(kid, "file", "normal")
				kid.ToolTipText = fullName

		def sortNode(arg, currDir, fNames):
			if currDir in self._pathNode:
				self.SortChildren(self._pathNode[currDir].itemID)

		if wildcard and not isinstance(wildcard, (list, tuple)):
			# single string passed
			wildcard = [wildcard]
		if ignored and not isinstance(ignored, (list, tuple)):
			# single string passed
			ignored = [ignored]
		arg = (wildcard, ignored, showHidden)
		os.path.walk(dirPath, addNode, arg)
		os.path.walk(dirPath, sortNode, None)
		if expand:
			self.expandAll()


	def _setAbsoluteFontZoom(self, newZoom):
		self._currFontZoom = newZoom
		for node in self.nodes:
			origFontSize = node._origFontSize = getattr(node, "_origFontSize", node.FontSize)
			fontSize = origFontSize + newZoom
			if fontSize > 1:
				node.FontSize = fontSize

		if self.Form is not None:
			dabo.ui.callAfterInterval(200, self.Form.layout)


	def treeFromStructure(self, stru, topNode=None):
		"""
		Given a sequence of items with a standard format,
		this will construct a tree structure and append it to
		the specified 'topNode'. If 'topNode' is None, the tree
		will be cleared, and a new structure containing only the
		passed info will be created. The info should be passed
		as a sequence of either lists or tuples, with the first
		element being the text to be displayed, and, if there are
		to be child nodes, the second being the child node
		information. If there are no children for that node, either
		do not include the second element, or set it to None.
		If there are child nodes, the child information will be
		recursively parsed.
		"""
		addRoot = (topNode is None)
		if addRoot:
			self.DeleteAllItems()
		if isinstance(stru[0], basestring):
			# We're at the end of the recursion. Just append the node
			self.appendNode(topNode, stru[0])
		else:
			for nodes in stru:
				txt = nodes[0]
				if addRoot:
					nd = self.setRootNode(txt)
					addRoot = False
				else:
					nd = self.appendNode(topNode, txt)
				try:
					kids = nodes[1]
				except IndexError:
					kids = None
				if kids:
					self.treeFromStructure(kids, nd)


	def addDummyData(self):
		"""For testing purposes!"""
		root = ["This is the root"]
		kid1 = ["First Child"]
		kid2 = ["Second Child"]
		kid3 = ["Third Child"]
		gk1 = ["Grandkid #1"]
		gk2 = ["Grandkid #2"]
		gk3 = ["Grandkid #3"]
		ggk1 = ["Great-Grandkid #1"]
		root.append([kid1, kid2, kid3])
		kid2.append([gk1, gk2, gk3])
		gk2.append(ggk1)
		self.treeFromStructure([root])
		### NOTE: This will also work
		# 		self.DeleteAllItems()
		# 		r = self.setRootNode("This is the root")
		# 		c1 = r.appendChild("First Child")
		# 		c2 = r.appendChild("Second Child")
		# 		c3 = r.appendChild("Third Child")
		# 		c21 = c2.appendChild("Grandkid #1")
		# 		c22 = c2.appendChild("Grandkid #2")
		# 		c23 = c2.appendChild("Grandkid #3")
		# 		c221 = c22.appendChild("Great-Grandkid #1")


	def getNodeForID(self, idval):
		"""Given a wx item ID, returns the corresponding node, or None."""
		try:
			ret = [nd for nd in self.nodes
					if nd.itemID == idval][0]
		except IndexError:
			ret = None
		return ret


	def getNodeUnderMouse(self, includeSpace=False, includeButton=True):
		"""
		Returns the node directly under the mouse, or None if the mouse is not
		over a node. If 'includeSpace' is True, the empty space to the right of the node
		is counted as part of the node. Likewise, if 'includeButton' is True, the
		area for the expanding/collapsing button is considered part of the node.
		Otherwise, it is considered to not be over any node.
		"""
		# The following wxPython constants are available:
		# 	wx.TREE_HITTEST_ABOVE: Above the client area.
		# 	wx.TREE_HITTEST_BELOW: Below the client area.
		# 	wx.TREE_HITTEST_NOWHERE: In the client area but below the last item.
		# 	wx.TREE_HITTEST_ONITEMBUTTON: On the button associated with an item.
		# 	wx.TREE_HITTEST_ONITEMICON: On the bitmap associated with an item.
		# 	wx.TREE_HITTEST_ONITEMINDENT: In the indentation associated with an item.
		# 	wx.TREE_HITTEST_ONITEMLABEL: On the label (string) associated with an item.
		# 	wx.TREE_HITTEST_ONITEMRIGHT: In the area to the right of an item.
		# 	wx.TREE_HITTEST_ONITEMSTATEICON: On the state icon for a tree view item that is in a user-defined state.
		# 	wx.TREE_HITTEST_TOLEFT: To the right of the client area.
		# 	wx.TREE_HITTEST_TORIGHT: To the left of the client area.
		ret = None
		mp = self.getMousePosition()
		idval, flag = self.HitTest(mp)
		overFlags = (wx.TREE_HITTEST_ONITEMICON |
				wx.TREE_HITTEST_ONITEMINDENT | wx.TREE_HITTEST_ONITEMLABEL)
		if includeSpace:
			overFlags = overFlags | wx.TREE_HITTEST_ONITEMRIGHT
		if includeButton:
			overFlags = overFlags | wx.TREE_HITTEST_ONITEMBUTTON
		if idval and (flag & overFlags):
			ret = self.getNodeForID(idval)
		return ret


	def getBaseNodeClass(cls):
		return dNode
	getBaseNodeClass = classmethod(getBaseNodeClass)


	# Event-handling code
	def __onTreeSel(self, evt):
		self.raiseEvent(dEvents.TreeSelection, evt)
	def __onKeyUp(self, evt):
		evt.Skip()
		if evt.GetKeyCode() in (316, 317, 318, 319):
			self._onWxHit(evt)
	def __onTreeItemCollapse(self, evt):
		self.raiseEvent(dEvents.TreeItemCollapse, evt)
	def __onTreeItemExpand(self, evt):
		self.raiseEvent(dEvents.TreeItemExpand, evt)


	def __onTreeMouseMove(self, evt):
		if self._useNodeToolTips:
			nd = self.getNodeUnderMouse()
			if nd:
				if nd.ToolTipText:
					self.ToolTipText = nd.ToolTipText
				else:
					self.ToolTipText = nd.Caption
			else:
				if self._storedToolTipText is not None:
					self.ToolTipText = self._storedToolTipText
				else:
					self.ToolTipText = ""


	def _getBaseNodes(self):
		if self.ShowRootNode:
			return [self._rootNode]
		else:
			return [nd for nd in self.nodes
					if nd.parent is not None
					and nd.parent.IsRootNode]


	def _getEditable(self):
		return self._hasWindowStyleFlag(wx.TR_EDIT_LABELS)

	def _setEditable(self, val):
		self._delWindowStyleFlag(wx.TR_EDIT_LABELS)
		if val:
			self._addWindowStyleFlag(wx.TR_EDIT_LABELS)


	def _getImageSize(self):
		return self._imageSize

	def _setImageSize(self, val):
		if self._constructed():
			self._imageSize = val
		else:
			self._properties["ImageSize"] = val


	def _getMultipleSelect(self):
		return self._hasWindowStyleFlag(wx.TR_MULTIPLE)

	def _setMultipleSelect(self, val):
		self._delWindowStyleFlag(wx.TR_MULTIPLE)
		self._delWindowStyleFlag(wx.TR_EXTENDED)
		self._delWindowStyleFlag(wx.TR_SINGLE)
		if val:
			self._addWindowStyleFlag(wx.TR_MULTIPLE)
			self._addWindowStyleFlag(wx.TR_EXTENDED)
		else:
			if self._constructed():
				self.lockDisplay()
				sel = self.Selection
				self.UnselectAll()
				self._addWindowStyleFlag(wx.TR_SINGLE)
				self.Selection = sel
				self.unlockDisplay()
			else:
				self._addWindowStyleFlag(wx.TR_SINGLE)


	def _getNodeClass(self):
		return self._nodeClass

	def _setNodeClass(self, val):
		if self._constructed():
			self._nodeClass = val
		else:
			self._properties["NodeClass"] = val


	def _getSelection(self):
		if self.MultipleSelect:
			ids = self.GetSelections()
			ret = [node for node in self.nodes
					if node.itemID in ids]
		else:
			itemID = self.GetSelection()
			if itemID:
				try:
					ret = [n for n in self.nodes
							if n.itemID == itemID][0]
				except IndexError:
					ret = None
			else:
				ret = None
		return ret

	def _setSelection(self, node):
		if self._constructed():
			self.UnselectAll()
			if not node:
				return
			if isinstance(node, (list, tuple)):
				if self.MultipleSelect:
					for itm in node:
						self.SelectItem(itm.itemID, True)
				else:
					if len(node) > 1:
						dabo.log.error(_("Attempting to select multiple nodes when MultipleSelect is False"))
					self.SelectItem(node[0].itemID)
			else:
				self.SelectItem(node.itemID)
		else:
			self._properties["Selection"] = node


	def _getShowButtons(self):
		return self._hasWindowStyleFlag(wx.TR_HAS_BUTTONS)

	def _setShowButtons(self, val):
		if val:
			self._delWindowStyleFlag(wx.TR_NO_BUTTONS)
			self._addWindowStyleFlag(wx.TR_HAS_BUTTONS)
		else:
			self._delWindowStyleFlag(wx.TR_HAS_BUTTONS)
			self._addWindowStyleFlag(wx.TR_NO_BUTTONS)
		if self._constructed():
			try:
				self.refresh()
			except AttributeError:
				# Control may not be constructed yet
				pass


	def _getShowLines(self):
		return not self._hasWindowStyleFlag(wx.TR_NO_LINES)

	def _setShowLines(self, val):
		self._delWindowStyleFlag(wx.TR_NO_LINES)
		if not val:
			self._addWindowStyleFlag(wx.TR_NO_LINES)
		if self._constructed():
			try:
				self.refresh()
			except AttributeError:
				# Control may not be constructed yet
				pass


	def _getShowRootNode(self):
		return not self._hasWindowStyleFlag(wx.TR_HIDE_ROOT)

	def _setShowRootNode(self, val):
		self._delWindowStyleFlag(wx.TR_HIDE_ROOT)
		if not val:
			self._addWindowStyleFlag(wx.TR_HIDE_ROOT)
		if self._constructed():
			try:
				self.refresh()
			except AttributeError:
				# Control may not be constructed yet
				pass


	def _getShowRootNodeLines(self):
		return self._hasWindowStyleFlag(wx.TR_LINES_AT_ROOT)

	def _setShowRootNodeLines(self, val):
		self._delWindowStyleFlag(wx.TR_LINES_AT_ROOT)
		if val:
			self._addWindowStyleFlag(wx.TR_LINES_AT_ROOT)
		if self._constructed():
			try:
				self.refresh()
			except AttributeError:
				# Control may not be constructed yet
				pass


	def _getUseNodeToolTips(self):
		return self._useNodeToolTips

	def _setUseNodeToolTips(self, val):
		if self._constructed():
			if val:
				self._storedToolTipText = self.ToolTipText
			else:
				if self._storedToolTipText is not None:
					self.ToolTipText = self._storedToolTipText
			self._useNodeToolTips = val
		else:
			self._properties["UseNodeToolTips"] = val


	BaseNodes = property(_getBaseNodes, None, None,
			_("""Returns the root node if ShowRootNode is True; otherwise,
			returns all the nodes who are not children of other nodes
			(read-only) (list of nodes)"""))

	Editable = property(_getEditable, _setEditable, None,
		_("""Specifies whether the tree labels can be edited by the user."""))

	ImageSize = property(_getImageSize, _setImageSize, None,
			_("Size of images added to the tree. Default=(15, 15)  (2-tuple of int)"))

	MultipleSelect = property(_getMultipleSelect, _setMultipleSelect, None,
		_("""Specifies whether more than one node may be selected at once."""))

	NodeClass = property(_getNodeClass, _setNodeClass, None,
			_("Class to use when creating nodes  (dNode)"))

	Selection = property(_getSelection, _setSelection, None,
		_("""Specifies which node or nodes are selected.

		If MultipleSelect is False, the currently selected node is specified. If MultipleSelect
		is True, a list of selected nodes is specified."""))

	ShowButtons = property(_getShowButtons, _setShowButtons, None,
		_("""Specifies whether +/- indicators are show at the left of parent nodes."""))

	ShowLines = property(_getShowLines, _setShowLines, None,
			_("Specifies whether lines are drawn between nodes.  (bool)"))

	ShowRootNode = property(_getShowRootNode, _setShowRootNode, None,
		_("""Specifies whether the root node is included in the treeview.

		There can be only one root node, so if you want several root nodes you can
		fake it by setting ShowRootNode to False. Now, your top child nodes have
		the visual indication of being sibling root nodes."""))

	ShowRootNodeLines = property(_getShowRootNodeLines, _setShowRootNodeLines, None,
		_("""Specifies whether vertical lines are shown between root siblings."""))

	UseNodeToolTips = property(_getUseNodeToolTips, _setUseNodeToolTips, None,
			_("""When True, the ToolTipText displayed is taken from the node.
			Default=False  (bool)"""))



	DynamicEditable = makeDynamicProperty(Editable)
	DynamicMultipleSelect = makeDynamicProperty(MultipleSelect)
	DynamicSelection = makeDynamicProperty(Selection)
	DynamicShowButtons = makeDynamicProperty(ShowButtons)
	DynamicShowLines = makeDynamicProperty(ShowLines)
	DynamicShowRootNode = makeDynamicProperty(ShowRootNode)
	DynamicShowRootNodeLines = makeDynamicProperty(ShowRootNodeLines)



class TestNode(dNode):
	def afterInit(self):
		self.ForeColor = "darkred"
		self.FontItalic = True
		self.FontSize += 3


class _dTreeView_test(dTreeView):
	def afterInit(self):
		self.NodeClass = TestNode
		self.addDummyData()
		self.expandAll()
		self.Hover = True
		self.ToolTipText = _("Default ToolTip for the Tree")
		self.ImageSize = (16, 16)

	def onHit(self, evt):
		print "Hit!"

	def onContextMenu(self, evt):
		print "Context menu on tree"

	def onMouseRightClick(self, evt):
		print "Mouse Right Click on tree"

	def onTreeSelection(self, evt):
		print "Selected node caption:", evt.EventData["selectedCaption"]

	def onTreeItemCollapse(self, evt):
		print "Collapsed node caption:", evt.EventData["selectedCaption"]

	def onTreeItemExpand(self, evt):
		print "Expanded node caption:", evt.EventData["selectedCaption"]

	def onTreeItemContextMenu(self, evt):
		itm = evt.itemID
		node = self.find(itm)[0]
		print "Context menu on item:", node.Caption

	def onTreeBeginDrag(self, evt):
		print "Beginning drag for %s" % evt.selectedCaption

	def onTreeEndDrag(self, evt):
		print "Ending drag for %s" % evt.selectedCaption



if __name__ == "__main__":
	from dabo.dApp import dApp
	import test

	class TreeViewTestForm(dabo.ui.dForm):
		def afterInit(self):
			mp = dabo.ui.dPanel(self)
			self.Sizer.append1x(mp)
			sz = mp.Sizer = dabo.ui.dSizer("v")
			tree = self.tree = _dTreeView_test(mp)
			sz.append1x(tree, border=12)
			sz.DefaultBorder = 7
			sz.DefaultBorderLeft = sz.DefaultBorderTop = True

			chk = dabo.ui.dCheckBox(mp, Caption="Editable",
					DataSource=tree, DataField="Editable")
			sz.append(chk, halign="Left")

			chk = dabo.ui.dCheckBox(mp, Caption="MultipleSelect",
					DataSource=tree, DataField="MultipleSelect")
			sz.append(chk, halign="Left")

			chk = dabo.ui.dCheckBox(mp, Caption="ShowButtons",
					DataSource=tree, DataField="ShowButtons")
			sz.append(chk, halign="Left")

			chk = dabo.ui.dCheckBox(mp, Caption="ShowLines",
					DataSource=tree, DataField="ShowLines")
			sz.append(chk, halign="Left")

			chk = dabo.ui.dCheckBox(mp, Caption="ShowRootNode",
					DataSource=tree, DataField="ShowRootNode")
			sz.append(chk, halign="Left")

			chk = dabo.ui.dCheckBox(mp, Caption="ShowRootNodeLines",
					DataSource=tree, DataField="ShowRootNodeLines")
			sz.append(chk, halign="Left")

			chk = dabo.ui.dCheckBox(mp, Caption="UseNodeToolTips",
					DataSource=tree, DataField="UseNodeToolTips")
			sz.append(chk, halign="Left")

			self.update()

			btnEx = dabo.ui.dButton(mp, Caption="Expand All")
			btnEx.bindEvent(dEvents.Hit, self.onExpandAll)
			btnCl = dabo.ui.dButton(mp, Caption="Collapse All")
			btnCl.bindEvent(dEvents.Hit, self.onCollapseAll)
			hsz = dabo.ui.dSizer("H")
			hsz.append(btnEx)
			hsz.appendSpacer(5)
			hsz.append(btnCl)
			sz.append(hsz)
			sz.appendSpacer(10)

		def onExpandAll(self, evt):
			self.tree.expandAll()

		def onCollapseAll(self, evt):
			self.tree.collapseAll()


	app = dApp()
	app.MainFormClass = TreeViewTestForm
	app.setup()
	app.start()
