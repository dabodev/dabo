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
import wx
import dabo.ui as ui

ui.loadUI("wx")

# Log all events except the really frequent ones:
logEvents = ["All", "Idle", "MouseMove"]

class Test(object):
	def __init__(self):
		self.app = wx.PySimpleApp()

	def runTest(self, classRef):
		frame = wx.Frame(None, -1, "")
		frame.SetSize((300,52))
		object = classRef(frame)
		object.debug = True
		object.LogEvents = logEvents
		frame.SetLabel("Test of %s" % object.Name)
		object.SetFocus()
		frame.Show()
		object.Show()
		self.app.MainLoop()

	def testAll(self):
		""" Create a dForm and populate it with example dWidgets. 
		"""
		frame = ui.dForm(name="formTest")
		frame.Width, frame.Height = 640, 480
		frame.Caption = "Test of all the dControls"
		frame.debug = True
		frame.LogEvents = logEvents

		panel = frame.addObject(ui.dPanel, "panelTest")

		labelWidth = 150

		vs = ui.dSizer("vertical")

		for object in (ui.dBitmapButton(panel),
					ui.dBox(panel),
					ui.dCheckBox(panel),
					ui.dCommandButton(panel),
					ui.dDateTextBox(panel),
					ui.dDropdownList(panel),
					ui.dEditBox(panel),
					ui.dGauge(panel),
					ui.dLine(panel),
					ui.dRadioGroup(panel),
					ui.dSlider(panel),
					ui.dSpinner(panel),
					ui.dTextBox(panel),
					ui.dToggleButton(panel)):
					
			bs = ui.dSizer("horizontal")
			label = ui.dLabel(panel, name="lbl%s" % object.Name, 
				style=wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE)
			label.Width = labelWidth

			label.Caption = "%s:" % object.Name
			bs.append(label)

			if isinstance(object, ui.dEditBox):
				layout = "expand"
			else:
				layout = "normal"

			object.debug = True

			bs.append(object, layout, 1)

			if isinstance(object, ui.dEditBox):
				vs.append(bs, "expand", 1)
			else:
				vs.append(bs, "expand")

		bs = ui.dSizer("horizontal")

		vs.append(bs, "expand")

		panel.SetSizer(vs)

		frame.SetSizer(ui.dSizer("vertical"))
		frame.GetSizer().append(panel, "expand")
		frame.Show()
		self.app.MainLoop()

if __name__ == "__main__":
	t = Test()
	t.testAll() 

