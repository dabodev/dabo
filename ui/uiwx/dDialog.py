import wx, dFormMixin

class dDialog(wx.Dialog, dFormMixin.dFormMixin):
	def __init__(self, parent=None, id=-1, title='', name='dDialog', *args, **kwargs):
		self._baseClass = dDialog

		pre = wx.PreDialog()
		self._beforeInit(pre)
		pre.Create(parent, id, title, name=name, style=pre.GetWindowStyle(), *args, **kwargs)

		self.PostCreate(pre)
		self.SetSizer(wx.BoxSizer(wx.VERTICAL))
		
		dFormMixin.dFormMixin.__init__(self)
		self._afterInit()
