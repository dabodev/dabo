import wx
import dSizer, dFormMixin

class dDialog(wx.Dialog, dFormMixin.dFormMixin):
	def __init__(self, parent=None, id=-1, title='', 
				style=wx.DEFAULT_DIALOG_STYLE, *args, **kwargs):
		self._baseClass = dDialog
		
		name, _explicitName = self._processName(kwargs, "dDialog")

		pre = wx.PreDialog()
		self._beforeInit(pre)
		pre.Create(parent, id, title, style=style|pre.GetWindowStyle(), *args, **kwargs)

		self.PostCreate(pre)
		self.Sizer = dSizer.dSizer("vertical")
		
		dFormMixin.dFormMixin.__init__(self, name=name, _explicitName=_explicitName)
		
		self._afterInit()
