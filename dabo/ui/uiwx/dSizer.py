import wx
import dabo
import dPemMixin
import dSizerMixin

class dSizer(wx.BoxSizer, dSizerMixin.dSizerMixin):
	def __init__(self, orientation="h", **kwargs ):
		# Convert Dabo orientation to wx orientation
		self._baseClass = dSizer
		
		orient = self._extractKey(kwargs, "Orientation", orientation)
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
