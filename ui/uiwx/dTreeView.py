import dabo
import re
import wx
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _


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
		
	
	def _getCap(self):
		return self.tree.GetItemText(self.id)
	def _setCap(self, val):
		self.tree.SetItemText(self.id, val)
	
	def _getChildren(self):
		return self.tree.getChildren(self)

	def _getSiblings(self):
		return self.tree.getSiblings(self)

	
	Caption = property(_getCap, _setCap, None,
			_("Returns/sets the text of this node.  (str)") )
			
	Children = property(_getChildren, None, None,
			_("List of all nodes for which this is their parent node.") )
		
	Siblings = property(_getSiblings, None, None,
			_("List of all nodes with the same parent node.") )
	
	

class dTreeView(wx.TreeCtrl, dcm.dControlMixin):
	_IsContainer = False
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dTreeView
		self.nodes = []

		style = self.extractKey(kwargs, "style")
		if not style:
			style = wx.TR_DEFAULT_STYLE

		preClass = wx.PreTreeCtrl
		dcm.dControlMixin.__init__(self, preClass, parent, properties, style=style, *args, **kwargs)
		
	
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
		
		
	def getChildren(self, node):
		""" Returns a list of all nodes that are child nodes of this node."""
		ret = [n for n in self.nodes
				if n.parent == node]
		return ret
	

	def getSiblings(self, node):
		""" Returns a list of all nodes at the same level as the specified
		node. The specified node is included in the list.
		"""
		ret = [n for n in self.nodes
				if n.parent == node.parent]
		return ret
	

	def find(self, srch):
		""" Searches the nodes collection for all nodes that match
		whose text matches the passed search value (if a text value
		was passed). If a wxPython TreeItemID object is passed, returns
		a list nodes matching that id value.
		Returns a list of matching nodes.
		"""
		ret = []
		if type(srch) in (unicode, str):
			ret = [n for n in self.nodes 
				if n.txt == srch ]
		elif isinstance(srch, wx.TreeItemId):
			ret = [n for n in self.nodes 
				if n.id == srch ]
		return ret
		
		
	def findPattern(self, srchPat):
		""" Allows for regexp pattern matching in order to find matching
		nodes using less than exact matches.
		Returns a list of matching nodes.
		"""
		ret = []
		if type(srchPat) in (unicode, str):
			ret = [n for n in self.nodes 
				if re.match(srchPat, n.txt) ]
		return ret


	def addDummyData(self):
		""" For testing purposes! """
		r = self.setRootNode("This is the root")
		c1 = r.appendChild("First Child")
		c2 = r.appendChild("Second Child")
		c3 = r.appendChild("Third Child")
		c21 = c2.appendChild("Grandkid #1")
		c22 = c2.appendChild("Grandkid #2")
		c23 = c2.appendChild("Grandkid #3")
		c221 = c22.appendChild("Great-Grandkid #1")
		
	
	def _getSel(self):
		id = self.GetSelection()
		ret = [ n for n in self.nodes
				if n.id == id]
		return ret[0]
	def _setSel(self, node):
		self.SelectItem(node.id)
	
	
	Selection = property(_getSel, _setSel, None,
			_("Returns the currently selected node   (dNode)") )
		
			
if __name__ == "__main__":
	import test
	
	class TestTree(dTreeView):
		def afterInit(self): 
			self.addDummyData()
		
		
	test.Test().runTest(TestTree)
