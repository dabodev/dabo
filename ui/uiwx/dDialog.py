import wx
import dSizer, dFormMixin

class dDialog(wx.Dialog, dFormMixin.dFormMixin):
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dDialog
		preClass = wx.PreDialog
		
		kwargs["style"] = wx.DEFAULT_DIALOG_STYLE
		dFormMixin.dFormMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

		self.Sizer = dSizer.dSizer("vertical")
		
