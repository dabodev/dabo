import dabo
dabo.ui.loadUI("wx")
from dabo.lib.ListSorter import ListSorter
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
		self.listBox = ListSorter(self, Choices=self._itms)
		self.Sizer.append(self.listBox, 1, "expand", border=30, borderFlags="all")
		self.layout()


	def _getChoices(self):
		try:
			return self.listBox.Choices
		except:
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
	
	def closeIt(evt):
		# Print out the sorted order
		print "Sorted:", app.MainForm.Choices
		# Need to do this, as dialogs don't release when closed
		app.MainForm.release()
	app.MainForm.bindEvent(dEvents.Deactivate, closeIt)
	
	app.start()
	
