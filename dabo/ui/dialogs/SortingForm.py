# -*- coding: utf-8 -*-
import dabo.ui
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class SortingForm(dabo.ui.dOkCancelDialog):
	"""This class affords a simple way to order a list of items. """
	def __init__(self, parent=None, Choices=[], *args, **kwargs):
		self._itms = list(Choices)
		super(SortingForm, self).__init__(parent=parent, *args, **kwargs)
		self.AutoSize = False
		self.Size = (330, 300)
		self._listCaption = ""


	def addControls(self):
		self.listBox = dabo.ui.dEditableList(self, Caption=self._listCaption,
				Choices=self._itms, Editable=False, CanDelete=False,
				CanAdd=False)
		self.Sizer.append(self.listBox, 1, "expand", border=30, borderSides="all")
		self.layout()


	def _getChoices(self):
		try:
			return self.listBox.Choices
		except AttributeError:
			return self._itms

	def _setChoices(self, chc):
		self._itms = self.listBox.Choices = list(chc)


	def _getListCaption(self):
		return self.listBox.Caption

	def _setListCaption(self, val):
		try:
			self.listBox.Caption = val
		except AttributeError:
			self._listCaption = val


	ListCaption = property(_getListCaption, _setListCaption, None,
			_("Caption for the sorting list  (str)"))

	Choices = property(_getChoices, _setChoices, None,
			_("Items in the list to sort.   (list)") )


if __name__ == "__main__":
	from dabo.dApp import dApp
	class DummyForm(dabo.ui.dForm):
		def onActivate(self, evt):
			self.Visible = False
			dlg = SortingForm(self, Caption="Fruit Sort",
					ListCaption="Which do you like best?",
					Choices = ["apple", "pear", "banana", "peach",
					"strawberry", "lime"])
			dlg.show()
			if dlg.Accepted:
				print "Sorted:", dlg.Choices
			else:
				print "Cancel was pressed"
			dlg.release()
			dabo.ui.callAfter(self.release)

	app = dApp()
	app.MainFormClass = DummyForm
	app.start()

