import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as dControlMixin

class dPanel(wx.Panel, dControlMixin.dControlMixin):
	""" This is a basic container for controls.

	Panels can contain subpanels to unlimited depth, making them quite
	flexible for many uses. Consider laying out your forms on panels
	instead, and then adding the panel to the form.
	"""

	def __init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL, *args, **kwargs):

		self._baseClass = dPanel

		name, _explicitName = self._processName(kwargs, "dPanel")
		
		pre = wx.PrePanel()
		self._beforeInit(pre)
		pre.Create(parent, id=id, style=style|pre.GetWindowStyle(), *args, **kwargs)

		self.PostCreate(pre)
		
		dControlMixin.dControlMixin.__init__(self, name, _explicitName=_explicitName)

		self._afterInit()


class dScrollPanel(wx.ScrolledWindow, dControlMixin.dControlMixin):
	""" This is a basic container for controls that allows scrolling.

	Panels can contain subpanels to unlimited depth, making them quite
	flexible for many uses. Consider laying out your forms on panels
	instead, and then adding the panel to the form.
	"""
	def __init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL, *args, **kwargs):

		self._baseClass = dScrollPanel

		name, _explicitName = self._processName(kwargs, "dScrollPanel")
		
		pre = wx.PreScrolledWindow()
		self._beforeInit(pre)
		pre.Create(parent, id=id, style=style|pre.GetWindowStyle(), *args, **kwargs)

		self.PostCreate(pre)
		
		dControlMixin.dControlMixin.__init__(self, name, _explicitName=_explicitName)
		
		self.SetScrollbars(10, 10, -1, -1)
		self._afterInit()
