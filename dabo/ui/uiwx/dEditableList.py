import wx
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class dEditableList(wx.gizmos.EditableListBox, 
		dcm.dControlMixin):
	"""Creates an editable list box, complete with buttons to control
	editing, adding/deleting items, and re-ordering them.
	"""	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dEditableList
		preClass = wx.gizmos.EditableListBox
		self._canAdd = self._extractKey((kwargs, properties), "CanAdd", True)
		self._canDelete = self._extractKey((kwargs, properties), "CanDelete", True)
		self._canOrder = self._extractKey((kwargs, properties), "CanOrder", True)
		self._editable = self._extractKey((kwargs, properties), "Editable", True)
		style = self._extractKey((kwargs, properties), "style", 0)
		if self._canAdd:
			style = style  | wx.gizmos.EL_ALLOW_NEW
		if self._editable:
			style = style  | wx.gizmos.EL_ALLOW_EDIT
		if self._canDelete:
			style = style  | wx.gizmos.EL_ALLOW_DELETE
		kwargs["style"] = style

		dcm.dControlMixin.__init__(self, preClass, parent, properties, 
				*args, **kwargs)

		# Set the reference to the main panel. 
		self._panel = [pp for pp in self.Children
				if isinstance(pp, wx.Panel)][0]
		# Store references to the different buttons
		self._editButton = self.GetEditButton()
		self._addButton = self.GetNewButton()
		self._deleteButton = self.GetDelButton()
		self._upButton = self.GetUpButton()
		self._downButton = self.GetDownButton()

	
	def GetValue(self):
		"""This control doesn't natively support values, as it is designed
		to simply order and/or edit the list. We need to provide this so that 
		the dControlMixin code which calls GetValue() doesn't barf.
		"""
		return None
	
	
	def layout(self):
		"""Calling the native Layout() method isn't sufficient, as it doesn't seem
		to call the top panel's Layout(). So we'll do it manually.
		"""
		self.Layout()
		self._panel.Layout()
		

	## property get/set methods follow ##
	def _getCanAdd(self):
		return self._canAdd

	def _setCanAdd(self, val):
		if self._constructed():
			self._canAdd = val
			self._addButton.Show(val)
			self.layout()
		else:
			self._properties["CanAdd"] = val


	def _getCanDelete(self):
		return self._canDelete

	def _setCanDelete(self, val):
		if self._constructed():
			self._canDelete = val
			self._deleteButton.Show(val)
			self.layout()
		else:
			self._properties["CanDelete"] = val


	def _getCanOrder(self):
		return self._canOrder

	def _setCanOrder(self, val):
		if self._constructed():
			self._canOrder = val
			self._upButton.Show(val)
			self._downButton.Show(val)
		else:
			self._properties["CanOrder"] = val
		self.layout()
	
	
	def _getCaption(self):
		return self._panel.GetChildren()[0].GetLabel()

	def _setCaption(self, val):
		if self._constructed():
			self._panel.GetChildren()[0].SetLabel(val)
		else:
			self._properties["Caption"] = val


	def _getChoices(self):
		return self.GetStrings()

	def _setChoices(self, val):
		if self._constructed():
			self.SetStrings(val)
		else:
			self._properties["Choices"] = val


	def _getEditable(self):
		return self._editable

	def _setEditable(self, val):
		if self._constructed():
			self._editable = val
			self._editButton.Show(val)
			self.layout()
		else:
			self._properties["Editable"] = val


	CanAdd = property(_getCanAdd, _setCanAdd, None,
			_("Determines if the user can add new entries to the list  (bool)"))
	
	CanDelete = property(_getCanDelete, _setCanDelete, None,
			_("Determines if the user can delete entries from the list  (bool)"))

	CanOrder = property(_getCanOrder, _setCanOrder, None,
			_("Determines if the user can re-order items  (bool)"))
	
	Caption = property(_getCaption, _setCaption, None,
			_("Text that appears in the top panel of the control  (str)"))
	
	Choices = property(_getChoices, _setChoices, None,
			_("List that contains the entries in the control  (list)"))
	
	Editable = property(_getEditable, _setEditable, None,
			_("Determines if the user can change existing entries  (bool)"))
	
