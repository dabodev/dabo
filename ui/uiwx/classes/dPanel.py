import wx, dControlMixin

class dPanel(wx.Panel, dControlMixin.dControlMixin):
	''' This is a basic container for controls.

	Panels can contain subpanels to unlimited depth, making them quite
	flexible for many uses. Consider laying out your forms on panels
	instead, and then adding the panel to the form.
	'''

	def __init__(self, parent, id=-1, name="dPanel", style=wx.TAB_TRAVERSAL, *args, **kwargs):

		self._baseClass = dPanel

		pre = wx.PrePanel()
		self.beforeInit(pre)                  # defined in dPemMixin
		pre.Create(parent, id=id, name=name, style=style|pre.GetWindowStyle(), *args, **kwargs)

		self.PostCreate(pre)
		
		dControlMixin.dControlMixin.__init__(self, name)

		self.afterInit()                      # defined in dPemMixin
