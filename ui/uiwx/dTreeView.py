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
		self.id = id
		self.txt = txt
		self.parent = parent
	
	def appendChild(self, txt):
		return self.tree.appendNode(self, txt)



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
	
	
	def find(self, srch):
		""" Searches the nodes collection for all nodes that match
		whose text matches the passed search value.
		Returns a list of matching nodes.
		"""
		ret = []
		if type(srch) == str:
			ret = [n for n in self.nodes 
				if n.txt == srch ]
		return ret
		
		
	def findPattern(self, srchPat):
		""" Allows for regexp pattern matching in order to find matching
		nodes using less than exact matches.
		Returns a list of matching nodes.
		"""
		ret = []
		if type(srchPat) == str:
			ret = [n for n in self.nodes 
				if re.match(srchPat, n.txt) ]
		return ret


	def addDummyData(self):
		r = self.setRootNode("This is the root")
		c1 = r.appendChild("First Child")
		c2 = r.appendChild("Second Child")
		c3 = r.appendChild("Third Child")
		c21 = c2.appendChild("Grandkid #1")
		c22 = c2.appendChild("Grandkid #2")
		c23 = c2.appendChild("Grandkid #3")
		c221 = c22.appendChild("Great-Grandkid #1")
		
		

		
		
			
if __name__ == "__main__":
	import test
	
	class TestTree(dTreeView):
		def afterInit(self): 
			self.addDummyData()
		
		
	test.Test().runTest(TestTree)
