import wx
import dControlMixin as cm

class dBox(wx.StaticText, cm.dControlMixin):
	""" Create a static (not data-aware) box.
	"""
	def __init__(self, parent, id=-1, label="", pos=(-1, -1), size=(-1, -1), name='dBox', style=0, *args, **kwargs):

		self._baseClass = dBox
		
		pre = wx.PreStaticBox()
		self._beforeInit(pre)                  # defined in dPemMixin
		
		pre.Create(parent, id, label, pos, size, name=name, style=style | pre.GetWindowStyle(), *args, **kwargs)
		self.PostCreate(pre)

		cm.dControlMixin.__init__(self, name)
		self._afterInit()                      # defined in dPemMixin


	def initEvents(self):
		# init the common events:
		cm.dControlMixin.initEvents(self)

		# init the widget's specialized event(s):

	# property get/set functions


if __name__ == "__main__":
	import test
	test.Test().runTest(dBox)
