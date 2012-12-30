# -*- coding: utf-8 -*-
""" test.py

A simple reusable unit testing framework, used by the base class files when run
as scripts instead of imported as modules.

If you execute, say:
	python dTextBox.py

The dTextBox.py's main section will instantiate class Test and do a simple unit
test of dTextBox.

If you instead run this test.py as a script, a form will be instantiated with
all the dControls.
"""
import dabo
import dabo.ui as ui
from dabo.dApp import dApp
import dabo.dEvents as dEvents

ui.loadUI("tk")

class Test(object):
	def __init__(self):
		self.app = dApp()
		self.app.LogEvents = ["All"]

	def runTest(self, classRef):
		self.app.setup()
		frame = self.app.MainForm
		object = classRef(frame)
		object.debug = True
		self.app.start()

	def testAll(self):
		""" Create a dForm and populate it with example dWidgets.
		"""
		self.app.setup()
		frame = self.app.MainForm
		frame.Size = (340, 120)
		frame.Caption = "Test of all the dControls"
		frame.debug = True
		frame.LogEvents = ["All"]

		panel = frame.addObject(ui.dPanel, "panelTest")
		panel.LogEvents = ["All"]

		labelWidth = 150

		for objClass in (ui.dCheckBox,):

			label = ui.dLabel(panel)
			label.Width = labelWidth

			obj = objClass(panel)
			obj.bindEvent(dEvents.Hit, self.objHit)
			label.Caption = "%s:" % objClass.__name__

			obj.debug = True
			obj.LogEvents = ["All"]

		self.app.start()

	def objHit(self, evt):
		print "hit!", evt

if __name__ == "__main__":
	t = Test()
	t.testAll()

