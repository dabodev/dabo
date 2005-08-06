import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
import dabo.dConstants as k
from dabo.dLocalize import _


class ListSorter(dabo.ui.dPanel):
	def __init__(self, parent, Choices=[], *args, **kwargs):
		self._itms = Choices
		super(ListSorter, self).__init__(parent=parent, *args, **kwargs)
		
	def afterInit(self):
		self.Sizer = dabo.ui.dSizer("v")
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
		self.Sizer.append(hsz, 1, "expand")
		
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


def main():
	class TestForm(dabo.ui.dForm):
		def afterInit(self):
			self.lst = ListSorter(self, Choices=["apple", "pear", "banana", "peach", "strawberry", "lime"])
			btn = dabo.ui.dButton(self, Caption="Bye")
			btn.bindEvent(dabo.dEvents.Hit, self.onButton)
			self.Sizer.append(self.lst, 1, "x")
			self.Sizer.append(btn, halign="center")
		
		def onButton(self, evt):
			ch = self.lst.Choices
			print "Choices:"
			for itm in ch:
				print "\t", itm
			self.close()

	app = dabo.dApp()
	app.MainFormClass = TestForm
	app.setup()
	app.start()

	
if __name__ == "__main__":
	main()

