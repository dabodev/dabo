# -*- coding: utf-8 -*-
import wx
import dabo
import dPemMixin
import dSizerMixin

class dSizer(dSizerMixin.dSizerMixin, wx.BoxSizer):
	def __init__(self, *args, **kwargs ):
		# Convert Dabo orientation to wx orientation
		self._baseClass = dSizer
		self._border = 0
		self._parent = None

		properties = self._extractKey(kwargs, "properties", {})
		fixedOrient = self._extractKey(kwargs, "FixedOrientation")
		if fixedOrient:
			orient = fixedOrient
		else:
			if args:
				# The orientation was passed as a standalone argument
				kwargs["Orientation"] = args[0]
				args = tuple(args[1:])

			orient = self._extractKey((kwargs, properties), "Orientation", "h")
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
			# Some kwargs haven't been handled.
			bad = ", ".join(kwargs.keys())
			raise TypeError("Invalid keyword arguments passed to dSizer: %s" % bad)

		dSizerMixin.dSizerMixin.__init__(self, *args, **kwargs)


	def getBorderedClass(self):
		"""Return the class that is the border sizer version of this class."""
		return dabo.ui.dBorderSizer



class dSizerV(dSizer):
	def __init__(self, *args, **kwargs ):
		kwargs["FixedOrientation"] = "V"
		super(dSizerV, self).__init__(*args, **kwargs)



class dSizerH(dSizer):
	def __init__(self, *args, **kwargs ):
		kwargs["FixedOrientation"] = "H"
		super(dSizerH, self).__init__(*args, **kwargs)

if __name__ == "__main__":
	s = dSizer()
