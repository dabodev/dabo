""" dMenu.py """
import wx
import dPemMixin as pm

class dMenu(wx.Menu, pm.dPemMixin):
	def __init__(self, mainForm=None):
		if mainForm:
			self.mainForm = mainForm
			self.actionList = mainForm.Application.actionList
		#dMenu.doDefault()
		super(dMenu, self).__init__()
