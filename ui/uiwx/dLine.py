import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm

class dLine(wx.StaticLine, cm.dControlMixin):
	""" Create a horizontal or vertical line.

	If Orientation is "Vertical", Height refers to the length of the line. 
  If Orientation is "Horizontal", Width refers to the length of the line.
	The other value refers to how wide the control is, which affects how much
	buffer space will enclose the line, which will appear in the center of
	this space.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dLine
		preClass = wx.PreStaticLine
		
		# Set the minimum initial Height and Width to 1.
## pkm: no, don't do this: it overrides whatever was set in a subclass initProperties()
#		if kwargs.has_key("Width"):
#			kwargs["Width"] = max(1, kwargs["Width"])
#		else:
#			kwargs["Width"] = 1
#		if kwargs.has_key("Height"):
#			kwargs["Height"] = max(1, kwargs["Height"])
#		else:
#			kwargs["Height"] = 1
		
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
	
	
	def _initEvents(self):
		super(dLine, self)._initEvents()
		
		
	# property get/set functions
	def _getOrientation(self):
 		if self._hasWindowStyleFlag(wx.LI_VERTICAL):
			return "Vertical"
		else:
			return "Horizontal"

	def _setOrientation(self, value):
		# Note: Orientation must be set before object created.
		self._delWindowStyleFlag(wx.LI_VERTICAL)
		self._delWindowStyleFlag(wx.LI_HORIZONTAL)

		value = str(value)

		if value == "Vertical":
			self._addWindowStyleFlag(wx.LI_VERTICAL)
		elif value == "Horizontal":
			self._addWindowStyleFlag(wx.LI_HORIZONTAL)
		else:
			raise ValueError, ("The only possible values are "
			                   "'Horizontal' and 'Vertical'.")

	# property definitions follow:
	Orientation = property(_getOrientation, _setOrientation, None,
						"Specifies the Orientation of the line. (str) \n"
						"   Horizontal (default) \n"
						"   Vertical"
						"This is determined by the Width and Height properties. "
						"If the Width is greater than the Height, it will be Horizontal. "
						"Otherwise, it will be Vertical.")


class _dLine_test(dLine):
	def initProperties(self):
		self.Orientation = "Horizontal"
		self.Width = 200
		self.Height = 10

if __name__ == "__main__":
	import test
	test.Test().runTest(_dLine_test)
