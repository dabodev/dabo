import wx
import dabo
import dPemMixin

class dSizer(wx.BoxSizer):
	def __init__(self, orientation="h"):
		# Convert Dabo orientation to wx orientation
		if orientation[0].lower() == "v":
			orientation = wx.VERTICAL
		else:
			orientation = wx.HORIZONTAL
		wx.BoxSizer.__init__(self, orientation)

	
	def add(self, item, layout="normal", proportion=0, alignment=("top", "left"), 
		border=0, borderFlags=("all",)):
		"""Add an object or a spacer to the sizer.
		
		layout: 
			"expand": The object will expand to fill in the extra space
			"fixed": The object will not be resized
			"normal": The sizer will determine how to lay out the object. (default)
			
		proportion: The relative space this object should get in relation to the 
			other objects. Default has all objects getting 0, equal share.
			
		alignment: The horizontal and vertical alignment of the object in the sizer.
			This is a tuple: set it like ("left", "top") or ("center", "middle").
			
		border: The width of the border. Default is 0, no border.
		
		borderFlags: A tuple containing the locations to draw the border, such as
			("all") or ("top", "left", "bottom"). Default is ("all").
			
		For the most common usage of adding an object to the sizer, just do:
			
			sizer.add(object)
			
			or
			
			sizer.add(object, "expand")
			
		"""
		# I purposely rearranged the order of parameters for the most common
		# use case of self.sizer.add(object, dabo.EXPAND).
		if type(item) == type(tuple()):
			# spacer
			self.Add(item)
		else:
			# item is the window to add to the sizer
			_wxFlags = 0
			for flag in [flag.lower() for flag in alignment]:
				if flag == "left":
					_wxFlags = _wxFlags | wx.ALIGN_LEFT
				elif flag == "right":
					_wxFlags = _wxFlags | wx.ALIGN_RIGHT
				elif flag == "center":
					_wxFlags = _wxFlags | wx.ALIGN_CENTER
				elif flag == "top":
					_wxFlags = _wxFlags | wx.ALIGN_TOP
				elif flag == "bottom":
					_wxFlags = _wxFlags | wx.ALIGN_BOTTOM
				elif flag == "middle":
					_wxFlags = _wxFlags | wx.ALIGN_CENTER_VERTICAL
					
			for flag in [flag.lower() for flag in borderFlags]:
				if flag == "left":
					_wxFlags = _wxFlags | wx.LEFT
				elif flag == "right":
					_wxFlags = _wxFlags | wx.RIGHT
				elif flag == "top":
					_wxFlags = _wxFlags | wx.TOP
				elif flag == "bottom":
					_wxFlags = _wxFlags | wx.BOTTOM
				elif flag == "all":
					_wxFlags = _wxFlags | wx.ALL
					
			if layout.lower() == "expand":
				_wxFlags = _wxFlags | wx.EXPAND
			elif layout.lower() == "fixed":
				_wxFlags = _wxFlags | wx.FIXED_MINSIZE
				
			self.Add(item, proportion, _wxFlags, border)
			
		
 	def _getOrientation(self):
		o = self.GetOrientation()
		
		if o == wx.VERTICAL:
			return "Vertical"
		elif o == wx.HORIZONTAL:
			return "Horizontal"
		else:
			return "?"
			
	def _setOrientation(self, val):
		if val[0].lower() == "v":
			self.SetOrientation(wx.VERTICAL)
		else:
			self.SetOrientation(wx.HORIZONTAL)
			
	Orientation = property(_getOrientation, _setOrientation, None, 
		"Sets the orientation of the sizer, either 'Vertical' or 'Horizontal'.")
		
if __name__ == "__main__":
	s = dSizer()
	