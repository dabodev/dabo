""" dMenuBar.py """
import wx

class dMenuBar(wx.MenuBar):
	_IsContainer = False
	
	def __init__(self, frm=None):
		super(dMenuBar, self).__init__()
		self._parent = frm

	def prepend(self, menu, prompt):
		return self.addOne(self.Prepend, menu, prompt)
	def append(self, menu, prompt):
		return self.addOne(self.Append, menu, prompt)
	def addOne(self, addFunc, menu, prompt):
		itm = addFunc(menu, prompt)
		return itm
		
	def insert(self, pos, menu, prompt):
		self.Insert(pos, menu, prompt)

	def getMenu(self, cap):
		return self.GetMenu(self.FindMenu(cap))
