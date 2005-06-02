import wx
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
import dabo.dException as dException
from dabo.dLocalize import _, n_
import dControlMixin as dcm


class dStatusBar(wx.StatusBar, dcm.dControlMixin):
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dStatusBar
		preClass = wx.PreStatusBar
		dcm.dControlMixin.__init__(self, preClass, parent, properties, 
				*args, **kwargs)

