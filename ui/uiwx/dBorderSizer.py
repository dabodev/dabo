import wx
import dabo
import dPemMixin
import dSizerMixin

class dBorderSizer(wx.StaticBoxSizer, dSizerMixin.dSizerMixin):
	def __init__(self, box, orientation="h"):
		# Make sure that they got the params in the right order
		if type(box) == type(""):
			box, orientation = orientation, box
		if not isinstance(box, wx.StaticBox):
			raise dException.dException, "Must pass an instance of a box to dBorderSizer"
		# Convert Dabo orientation to wx orientation
		if orientation[0].lower() == "v":
			orientation = wx.VERTICAL
		else:
			orientation = wx.HORIZONTAL
		wx.StaticBoxSizer.__init__(self, box, orientation)
	
		
if __name__ == "__main__":
	s = dBorderSizer()
	

