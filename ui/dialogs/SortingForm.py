import dabo
import dabo.lib
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
import dabo.dConstants as k
from dabo.dLocalize import _


class SortingForm(dabo.ui.dOkCancelDialog):
	"""This class affords a simple way to order a list of items. """
	def __init__(self, parent=None, Choices=[]):
		self._itms = list(Choices)
		super(SortingForm, self).__init__(parent=parent)
		self.AutoSize = False
		self.Size = (330, 300)
	
	
	def addControls(self):
		self.listBox = dabo.lib.ListSorter(self, Choices=self._itms)
		self.Sizer.append(self.listBox, 1, "expand", border=30, borderFlags="all")
		self.layout()


	def _getChoices(self):
		return self._itms
	def _setChoices(self, chc):
		self._itms = self.listBox.Choices = list(chc)
		
	Choices = property(_getChoices, _setChoices, None,
			_("Items in the list to sort.   (list)") )




if __name__ == "__main__":
	app = dabo.dApp()
	app.MainFormClass = SortingForm
	app.setup()
	app.MainForm.Choices = ["apple", "pear", "banana", "peach", "strawberry", "lime"]
	
	# Need to do this, as dialogs don't release when closed
	def closeIt(evt):
		app.MainForm.release()
	app.MainForm.bindEvent(dEvents.Deactivate, closeIt)
	
	app.start()
	