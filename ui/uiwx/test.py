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
import dabo.ui.uiwx as ui

class Test(object):
	def __init__(self):
		self.app = wx.PySimpleApp()

	def runTest(self, classRef):
		frame = wx.Frame(None, -1, "")
		frame.SetSize((300,52))
		object = classRef(frame)
		object.debug = True
		object.LogEvents = ["All"]
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
		frame.LogEvents = ["All"]

		panel = frame.addObject(ui.dPanel, "panelTest")
		panel.LogEvents = ["All"]

		labelWidth = 150

		vs = wx.BoxSizer(wx.VERTICAL)

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
					
			bs = wx.BoxSizer(wx.HORIZONTAL)
			label = ui.dLabel(panel, name="lbl%s" % object.Name, 
				style=wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE)
			label.Width = labelWidth

			label.Caption = "%s:" % object.Name
			bs.Add(label)

			if isinstance(object, ui.dEditBox):
				expandFlags = wx.EXPAND
			else:
				expandFlags = 0

			object.debug = True
			object.LogEvents = ["All"]

			bs.Add(object, 1, expandFlags | wx.ALL, 0)

			if isinstance(object, ui.dEditBox):
				vs.Add(bs, 1, wx.EXPAND)
			else:
				vs.Add(bs, 0, wx.EXPAND)

		bs = wx.BoxSizer(wx.HORIZONTAL)

		vs.Add(bs, 0, wx.EXPAND)

		panel.SetSizer(vs)        
		panel.GetSizer().Layout()

		frame.GetSizer().Add(panel, 1, wx.EXPAND)
		frame.GetSizer().Layout()
		frame.Show()
		self.app.MainLoop()

if __name__ == "__main__":
	t = Test()
	t.testAll() 

