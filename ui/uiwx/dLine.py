import wx
import dabo.ui.dControlMixin as cm

class dLine(wx.StaticLine, cm.dControlMixin):
	""" Create a static (not data-aware) line.
	"""
	def __init__(self, parent, id=-1, name='dLine', style=0, *args, **kwargs):

		self._baseClass = dLine

		pre = wx.PreStaticLine()
		self._beforeInit(pre)

		pre.Create(parent, id, name=name, style=style | pre.GetWindowStyle(), *args, **kwargs)
		self.PostCreate(pre)

		cm.dControlMixin.__init__(self, name)
		self._afterInit()


	def initEvents(self):
		dLine.doDefault()
		
		
	# property get/set functions
	def _getOrientation(self):
		if self.hasWindowStyleFlag(wx.LI_VERTICAL):
			return "Vertical"
		else:
			return "Horizontal"

	def _getOrientationEditorInfo(self):
		return {'editor': 'list', 'values': ['Horizontal', 'Vertical']}

	def _setOrientation(self, value):
		# Note: Orientation must be set before object created.
		self.delWindowStyleFlag(wx.LI_VERTICAL)
		self.delWindowStyleFlag(wx.LI_HORIZONTAL)

		value = str(value)

		if value == "Vertical":
			self.addWindowStyleFlag(wx.LI_VERTICAL)
		elif value == "Horizontal":
			self.addWindowStyleFlag(wx.LI_HORIZONTAL)
		else:
			raise ValueError, ("The only possible values are "
							"'Horizontal' and 'Vertical'.")

	# property definitions follow:
	Orientation = property(_getOrientation, _setOrientation, None,
						'Specifies the Orientation of the line. (str) \n'
						'   Horizontal (default) \n'
						'   Vertical')

if __name__ == "__main__":
	import test
	test.Test().runTest(dLine)
