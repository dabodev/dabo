import wx
import dabo
import dPemMixin
import dSizerMixin

class dSizer(wx.BoxSizer, dSizerMixin.dSizerMixin):
	def __init__(self, orientation="h"):
		# Convert Dabo orientation to wx orientation
		if orientation[0].lower() == "v":
			orientation = wx.VERTICAL
		else:
			orientation = wx.HORIZONTAL
		wx.BoxSizer.__init__(self, orientation)

		
if __name__ == "__main__":
	s = dSizer()
