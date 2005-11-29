import wx
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
import dabo.dException as dException
from dabo.dLocalize import _, n_
import dControlMixin as dcm


class dStatusBar(wx.StatusBar, dcm.dControlMixin):
	"""Creates a status bar, which displays information to the user.

	The status bar is displayed at the bottom of the form. Add the status bar
	to your form using form.StatusBar=dStatusBar().
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dStatusBar
		preClass = wx.PreStatusBar
		dcm.dControlMixin.__init__(self, preClass, parent, properties, 
				*args, **kwargs)

