import wx
import dSizer, dFormMixin

class dDialog(wx.Dialog, dFormMixin.dFormMixin):
	def __init__(self, parent=None, id=-1, title='', name="dDialog", 
				style=wx.DEFAULT_DIALOG_STYLE, *args, **kwargs):
		self._baseClass = dDialog

		pre = wx.PreDialog()
		self._beforeInit(pre)
		pre.Create(parent, id, title, name=name, 
				style=style|pre.GetWindowStyle(), *args, **kwargs)

		self.PostCreate(pre)
		self.Sizer = dSizer.dSizer("vertical")
		
		dFormMixin.dFormMixin.__init__(self)
		self._afterInit()
