import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm

class dPanel(wx.Panel, cm.dControlMixin):
	""" This is a basic container for controls.

	Panels can contain subpanels to unlimited depth, making them quite
	flexible for many uses. Consider laying out your forms on panels
	instead, and then adding the panel to the form.
	"""
	_IsContainer = True
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dPanel
		preClass = wx.PrePanel
		kwargs["style"] = wx.TAB_TRAVERSAL
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)


class dScrollPanel(wx.ScrolledWindow, cm.dControlMixin):
	""" This is a basic container for controls that allows scrolling.

	Panels can contain subpanels to unlimited depth, making them quite
	flexible for many uses. Consider laying out your forms on panels
	instead, and then adding the panel to the form.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dScrollPanel
		preClass = wx.PreScrolledWindow
		kwargs["style"] = wx.TAB_TRAVERSAL
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
		self.SetScrollbars(10, 10, -1, -1)
	
