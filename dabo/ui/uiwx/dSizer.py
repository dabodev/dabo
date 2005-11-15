import wx
import dabo
import dPemMixin
import dSizerMixin

class dSizer(wx.BoxSizer, dSizerMixin.dSizerMixin):
	def __init__(self, orientation="h", properties=None, **kwargs ):
		# Convert Dabo orientation to wx orientation
		self._baseClass = dSizer
		self._border = 0

		orient = self._extractKey(kwargs, "Orientation", orientation)
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
	
		
	def getItemProp(self, itm, prop):
		"""Get the current value of the specified property for the sizer item."""
		if prop == "Border":
			return itm.GetBorder()
		elif prop == "Proportion":
			return itm.GetProportion()
		else:
			# Property is in the flag setting.
			flag = itm.GetFlag()
			szClass = dabo.ui.dSizer
			if prop == "Expand":
				return bool(flag & szClass.expandFlag)
			elif prop == "Halign":
				if flag & szClass.centerFlag:
					return "Center"
				elif flag & szClass.rightFlag:
					return "Right"
				else: 		#if flag & szClass.leftFlag:
					return "Left"
			elif prop == "Valign":
				if flag & szClass.middleFlag:
					return "Middle"
				elif flag & szClass.bottomFlag:
					return "Bottom"
				else:		#if flag & szClass.topFlag:
					return "Top"


if __name__ == "__main__":
	s = dSizer()
