import dabo
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
		vsz = dabo.ui.dSizer("v")
		bUp = dabo.ui.dButton(self, Caption="Up")
		bDown = dabo.ui.dButton(self, Caption="Down")
		vsz.appendSpacer(1, 1)
		vsz.append(bUp)
		vsz.appendSpacer(4)
		vsz.append(bDown)
		vsz.appendSpacer(1, 1)
		hsz = dabo.ui.dSizer("h")
		hsz.append(vsz, 0, "expand", alignment="middle")
		bUp.bindEvent(dEvents.Hit, self.onUpButton)
		bDown.bindEvent(dEvents.Hit, self.onDownButton)
		
		self.listBox = dabo.ui.dListBox(self, Choices=self._itms, ValueMode="Position")
		hsz.append(self.listBox, "expand", 1)
		self.Sizer.append(hsz, 1, "expand", border=30, borderFlags="all")
		self.layout()


	def onUpButton(self, evt):
		self.reorder(-1)

	def onDownButton(self, evt):
		self.reorder(1)
	
	def reorder(self, dir):
		pos = self.listBox.Value
		if pos >= 0:
			maxlen = len(self._itms) -1
			choice = self._itms[pos]
			del self._itms[pos]
			newpos = min(maxlen, max(0, pos + dir) )
			self._itms.insert(newpos, choice)
			self.listBox.Choices = self._itms
			self.listBox.Value = newpos
	
	def alphaSort(self):
		""" Sort the list items alpahbetically."""
		self._itms.sort()
		self.listBox.Choices = self._itms

	
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
	