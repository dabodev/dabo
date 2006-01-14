import wx
import dabo
import dPemMixin
import dSizerMixin

class dSizer(wx.BoxSizer, dSizerMixin.dSizerMixin):
	def __init__(self, orientation="h", properties=None, **kwargs ):
		# Convert Dabo orientation to wx orientation
		self._baseClass = dSizer
		self._border = 0
		self._parent = None

		orient = self._extractKey((kwargs, properties), "Orientation", orientation)
		if orient[0].lower() == "v":
			orientation = wx.VERTICAL
		else:
			orientation = wx.HORIZONTAL
		wx.BoxSizer.__init__(self, orientation)

		self._properties = {}
		# The keyword properties can come from either, both, or none of:
		#    + the properties dict
		#    + the kwargs dict
		# Get them sanitized into one dict:
		if properties is not None:
			# Override the class values
			for k,v in properties.items():
				self._properties[k] = v
		properties = self._extractKeywordProperties(kwargs, self._properties)
		self.setProperties(properties)

		self.afterInit()


	def afterInit(self): pass	
	
		
if __name__ == "__main__":
	s = dSizer()
