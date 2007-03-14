import wx
import dabo
import dPemMixin
import dSizerMixin

class dSizer(dSizerMixin.dSizerMixin, wx.BoxSizer):
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
		
		if kwargs:
			bad = ", ".join(kwargs.keys())
			dabo.errorLog.write(("Invalid keyword arguments passed to dSizer: %s") % bad)

		self.afterInit()


	def afterInit(self): pass	
	
	
	def getBorderedClass(self):
		"""Return the class that is the border sizer version of this class."""
		return dabo.ui.dBorderSizer
	
		
if __name__ == "__main__":
	s = dSizer()
