import Tkinter, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("tk")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class dCheckBox(Tkinter.Checkbutton, dcm.dDataControlMixin):
	""" Allows visual editing of boolean values.
	"""
	def __init__(self, master=None, cnf={}, name="dCheckBox", *args, **kwargs):
		
		self._baseClass = dCheckBox

		self._beforeInit()
		Tkinter.Checkbutton.__init__(self, master, cnf, name=name, *args, **kwargs)

		dcm.dDataControlMixin.__init__(self, name)
		self._afterInit()

		self.pack()

	def initEvents(self):
		dCheckBox.doDefault()

		self.bindEvent(dEvents.MouseLeftClick, self._onTkHit)
		self.bindEvent(dEvents.KeyDown, self._onKeyDown)
		
	def _onKeyDown(self, event):
		char = event.EventData["keyChar"]
		if char is not None and ord(char) in (10,13,32):
			self._onTkHit(event)		
				
	def _getValue(self):
		try:
			v = self._value
		except AttributeError:
			v, self._value = False, False
			self.deselect()
		return v
		
	def _setValue(self, value):
		self._value = bool(value)
		if self._value:
			self.select()
		else:
			self.deselect()

		
	Value = property(_getValue, _setValue, None,
		'Specifies the current state of the control (the value of the field). (varies)')
	
	
	# property get/set functions
# 	def _getAlignment(self):
# 		if self.hasWindowStyleFlag(wx.ALIGN_RIGHT):
# 			return 'Right'
# 		else:
# 			return 'Left'
# 
# 	def _getAlignmentEditorInfo(self):
# 		return {'editor': 'list', 'values': ['Left', 'Right']}
# 
# 	def _setAlignment(self, value):
# 		self.delWindowStyleFlag(wx.ALIGN_RIGHT)
# 		if str(value) == 'Right':
# 			self.addWindowStyleFlag(wx.ALIGN_RIGHT)
# 		elif str(value) == 'Left':
# 			pass
# 		else:
# 			raise ValueError, "The only possible values are 'Left' and 'Right'."
# 
# 	# property definitions follow:
# 	Alignment = property(_getAlignment, _setAlignment, None,
# 						'Specifies the alignment of the text. (int) \n'
# 						'   Left  : Checkbox to left of text (default) \n'
# 						'   Right : Checkbox to right of text')

		
if __name__ == "__main__":
	class C(dCheckBox):
		def initEvents(self):
			C.doDefault()
			self.bindEvent(dEvents.Hit, self.onHit)
			self.bindEvent(dEvents.Hit, self.onHit2)
			
		def onHit(self, evt):
			print "hit!"
			#evt.stop()
		
		def onHit2(self, evt):
			print "hit2"
			
	import test
	test.Test().runTest(C)
