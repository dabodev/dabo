""" dMenuBar.py """
import wx

class dMenuBar(wx.MenuBar):
	_IsContainer = False
	
	def __init__(self, frm=None):
		super(dMenuBar, self).__init__()
		self._parent = frm
		self._menus = {}

	def append(self, menu, prompt):
		self.Append(menu, prompt)
		self._menus[prompt] = menu
	
	def insert(self, pos, menu, prompt):
		self.Insert(pos, menu, prompt)
		self._menus[prompt] = menu

	def getMenu(self, cap):
		ret = None
		if self._menus.has_key(cap):
			ret = self._menus[cap]
		return ret
