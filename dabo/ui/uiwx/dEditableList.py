# -*- coding: utf-8 -*-
import wx
import dabo
if __name__ == "__main__":
	import dabo.ui
	dabo.ui.loadUI("wx")
import dControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


class dEditableList(dcm.dControlMixin, wx.gizmos.EditableListBox):
	"""
	Creates an editable list box, complete with buttons to control
	editing, adding/deleting items, and re-ordering them.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dEditableList
		preClass = wx.gizmos.EditableListBox
		self._canAdd = self._extractKey((kwargs, properties, attProperties), "CanAdd", True)
		if isinstance(self._canAdd, basestring):
			self._canAdd = (self._canAdd == "True")
		self._canDelete = self._extractKey((kwargs, properties, attProperties), "CanDelete", True)
		if isinstance(self._canDelete, basestring):
			self._canDelete = (self._canDelete == "True")
		self._canOrder = self._extractKey((kwargs, properties, attProperties), "CanOrder", True)
		if isinstance(self._canOrder, basestring):
			self._canOrder = (self._canOrder == "True")
		self._editable = self._extractKey((kwargs, properties, attProperties), "Editable", True)
		style = self._extractKey((kwargs, properties, attProperties), "style", 0)
		if self._canAdd:
			style = style  | wx.gizmos.EL_ALLOW_NEW
		if self._editable:
			style = style  | wx.gizmos.EL_ALLOW_EDIT
		if self._canDelete:
			style = style  | wx.gizmos.EL_ALLOW_DELETE
		kwargs["style"] = style
		# References to the components of this control
		self._addButton = None
		self._deleteButton = None
		self._editButton = None
		self._downButton = None
		self._upButton = None
		self._panel = None

		dcm.dControlMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)


	def GetValue(self):
		"""
		This control doesn't natively support values, as it is designed
		to simply order and/or edit the list. We need to provide this so that
		the dControlMixin code which calls GetValue() doesn't barf.
		"""
		return None


	def layout(self):
		"""
		Calling the native Layout() method isn't sufficient, as it doesn't seem
		to call the top panel's Layout(). So we'll do it manually.
		"""
		self.Layout()
		self._Panel.Layout()
		if self.Application.Platform == "Win":
			self.refresh()


	## property get/set methods follow ##
	def _getAddButton(self):
		if self._addButton is None:
			self._addButton = self.GetNewButton()
		return self._addButton


	def _getCanAdd(self):
		return self._canAdd

	def _setCanAdd(self, val):
		if self._constructed():
			self._canAdd = val
			self._AddButton.Show(val)
			self.layout()
		else:
			self._properties["CanAdd"] = val


	def _getCanDelete(self):
		return self._canDelete

	def _setCanDelete(self, val):
		if self._constructed():
			self._canDelete = val
			self._DeleteButton.Show(val)
			self.layout()
		else:
			self._properties["CanDelete"] = val


	def _getCanOrder(self):
		return self._canOrder

	def _setCanOrder(self, val):
		if self._constructed():
			self._canOrder = val
			self._UpButton.Show(val)
			self._DownButton.Show(val)
		else:
			self._properties["CanOrder"] = val
		self.layout()


	def _getCaption(self):
		return self._Panel.GetChildren()[0].GetLabel()

	def _setCaption(self, val):
		if self._constructed():
			self._Panel.GetChildren()[0].SetLabel(val)
		else:
			self._properties["Caption"] = val


	def _getChoices(self):
		return self.GetStrings()

	def _setChoices(self, val):
		if self._constructed():
			self.SetStrings(val)
		else:
			self._properties["Choices"] = val


	def _getDeleteButton(self):
		if self._deleteButton is None:
			self._deleteButton = self.GetDelButton()
		return self._deleteButton



	def _getDownButton(self):
		if self._downButton is None:
			self._downButton = self.GetDownButton()
		return self._downButton



	def _getEditable(self):
		return self._editable

	def _setEditable(self, val):
		if self._constructed():
			self._editable = val
			self._EditButton.Show(val)
			self.layout()
		else:
			self._properties["Editable"] = val


	def _getEditButton(self):
		if self._editButton is None:
			self._editButton = self.GetEditButton()
		return self._editButton



	def _getPanel(self):
		if self._panel is None:
			self._panel = [pp for pp in self.Children
					if isinstance(pp, wx.Panel)][0]
		return self._panel



	def _getUpButton(self):
		if self._upButton is None:
			self._upButton = self.GetUpButton()
		return self._upButton



	_AddButton = property(_getAddButton, None, None,
			_("Reference to the new item button  (wx.Button)"))

	CanAdd = property(_getCanAdd, _setCanAdd, None,
			_("Determines if the user can add new entries to the list  (bool)"))
	DynamicCanAdd = makeDynamicProperty(CanAdd)

	CanDelete = property(_getCanDelete, _setCanDelete, None,
			_("Determines if the user can delete entries from the list  (bool)"))
	DynamicCanDelete = makeDynamicProperty(CanDelete)

	CanOrder = property(_getCanOrder, _setCanOrder, None,
			_("Determines if the user can re-order items  (bool)"))
	DynamicCanOrder = makeDynamicProperty(CanOrder)

	Caption = property(_getCaption, _setCaption, None,
			_("Text that appears in the top panel of the control  (str)"))
	DynamicCaption = makeDynamicProperty(Caption)

	Choices = property(_getChoices, _setChoices, None,
			_("List that contains the entries in the control  (list)"))

	_DeleteButton = property(_getDeleteButton, None, None,
			_("Reference to the delete item button  (wx.Button)"))

	_DownButton = property(_getDownButton, None, None,
			_("Reference to the move item down button  (wx.Button)"))

	Editable = property(_getEditable, _setEditable, None,
			_("Determines if the user can change existing entries  (bool)"))
	DynamicEditable = makeDynamicProperty(Editable)

	_EditButton = property(_getEditButton, None, None,
			_("Reference to the edit item button  (wx.Button)"))

	_Panel = property(_getPanel, None, None,
			_("""Reference to the panel that contains the caption
			and buttons  (wx.Panel)"""))

	_UpButton = property(_getUpButton, None, None,
			_("Reference to the move item up button  (wx.Button)"))



class _dEditableList_test(dEditableList):
	def afterInit(self):
		self.Choices = ["Johnny", "Joey", "DeeDee"]
		self.Caption = "Gabba Gabba Hey"

	def onDestroy(self, evt):
		# Need to check this, because apparently under the hood
		# wxPython destroys and re-creates the control when you
		# edit, add or delete an entry.
		if self._finito:
			print "Result:", self.Choices


if __name__ == "__main__":
	import test
	test.Test().runTest(_dEditableList_test)
