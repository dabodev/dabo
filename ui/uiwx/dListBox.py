import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _

class dListBox(wx.ListBox, dcm.dDataControlMixin):
	""" Allows presenting a choice of items for the user to choose from.
	"""
	def __init__(self, parent, id=-1, choices=["Dabo", "Default"], 
			style=0, selectionType="single", properties=None, *args, **kwargs):

		self._baseClass = dListBox
		properties = self.extractKeywordProperties(kwargs, properties)
		name, _explicitName = self._processName(kwargs, self.__class__.__name__)

		pre = wx.PreListBox()
		self._beforeInit(pre)
		
		selType = selectionType.lower()[:1]
		if selType == "m":
			# multiple selections
			style = style | wx.LB_MULTIPLE
		elif selType in ("e", "d"):
			# 'extended' or 'discontinuous'
			style = style | wx.LB_EXTENDED
		
		style = style | pre.GetWindowStyle()
		
 		pre.Create(parent, id, choices=choices, style=style, *args, **kwargs)

		self.PostCreate(pre)

		dcm.dDataControlMixin.__init__(self, name, _explicitName=_explicitName)
		
		self.setProperties(properties)
		self._afterInit()


	def initEvents(self):
		#dListBox.doDefault()
		super(dListBox, self).initEvents()
		
		# catch the wx event and raise the dabo event:
		self.Bind(wx.EVT_LISTBOX, self._onWxHit)
		

	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getValue(self):
		return self.GetStringSelection()
	def _setValue(self, value):
		if type(value) == type(""):
			try:
				self.SetStringSelection(value)
			except: pass		# maybe raise an error?
		elif type(value) == type(0):
			try:
				self.SetSelection(value)
			except: pass
	
	# Property definitions:
	Value = property(_getValue, _setValue, None,
			"Specifies the current state of the control (the value of the field). (varies)")

if __name__ == "__main__":
	import test
	test.Test().runTest(dListBox, choices=["soccer", "basketball", "golf", "baseball"])

