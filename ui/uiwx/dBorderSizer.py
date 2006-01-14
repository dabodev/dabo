import wx
import dabo
from dabo.dLocalize import _

dabo.ui.loadUI("wx")


class dBorderSizer(wx.StaticBoxSizer, dabo.ui.dSizerMixin):
	"""A BorderSizer is a regular box sizer, but with a visible box around
	the perimiter. You must either create the box first and pass it to the 
	dBorderSizer's constructor, or pass a parent object, and the box
	will be created for you in the constructor as a child object of the parent
	you passed.
	"""
	def __init__(self, box, orientation="h"):
		# Make sure that they got the params in the right order
		if isinstance(box, basestring):
			box, orientation = orientation, box
		if not isinstance(box, dabo.ui.dBox):
			try:
				prnt = box
				box = dabo.ui.dBox(prnt)
			except:
				raise dException.dException, "Must pass an instance of dBox or a parent object to dBorderSizer"
		# Convert Dabo orientation to wx orientation
		if orientation[0].lower() == "v":
			orientation = wx.VERTICAL
		else:
			orientation = wx.HORIZONTAL
		wx.StaticBoxSizer.__init__(self, box, orientation)
	

	def _getBox(self):
		return self.GetStaticBox()

	Box = property(_getBox, None, None,
			_("Reference to the box used in the sizer  (dBox)"))


	
class TestForm(dabo.ui.dForm):
	def afterInit(self):
		self.Sizer = dabo.ui.dSizer("v", Border=10)
		lbl = dabo.ui.dLabel(self, Caption="Button in BoxSizer Below", FontSize=16)
		self.Sizer.append(lbl, halign="center")
		sz = dBorderSizer(self, "v")
		self.Sizer.append1x(sz)
		btn = dabo.ui.dButton(self, Caption="Click")
		sz.append1x(btn)
		pnl = dabo.ui.dPanel(self, BackColor="seagreen")
		self.Sizer.append1x(pnl, border=18)
		
class _dBorderSizer_test(dBorderSizer):
	def __init__(self, *args, **kwargs):
		super(_dBorderSizer_test, self).__init__(box=bx, orientation="h", *args, **kwargs)




if __name__ == "__main__":
	app = dabo.dApp()
	app.MainFormClass = TestForm
	app.start()
