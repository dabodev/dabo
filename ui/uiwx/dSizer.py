import wx
import dabo
import dPemMixin
import dSizerMixin

class dSizer(wx.BoxSizer, dSizerMixin.dSizerMixin):
	_IsContainer = False
	
	def __init__(self, orientation="h", **kwargs ):
		# Convert Dabo orientation to wx orientation
		self._baseClass = dSizer
		
		orient = self.extractKey(kwargs, "Orientation", orientation)
		if orient[0].lower() == "v":
			orientation = wx.VERTICAL
		else:
			orientation = wx.HORIZONTAL
		wx.BoxSizer.__init__(self, orientation)

		for k,v in kwargs.items():
			try:
				exec("self.%s = %s" % (k,v))
			except: pass
		self.afterInit()

	def afterInit(self): pass	
		
if __name__ == "__main__":
	s = dSizer()
