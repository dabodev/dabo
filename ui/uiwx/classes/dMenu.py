""" dMenu.py """
import wx
import dPemMixin as pm

class dMenu(wx.Menu, pm.dPemMixin):
	def __init__(self, mainFrame=None):
		if mainFrame:
			self.mainFrame = mainFrame
			self.actionList = mainFrame.dApp.actionList
		dMenu.doDefault()
