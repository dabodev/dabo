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
		frame.SetSize((300,1))
		object = classRef(frame)
		frame.SetLabel("Test of %s" % object.GetName())
		object.SetFocus()
		frame.Show()
		object.Show()
		self.app.MainLoop()

	def testAll(self):
		""" Create a dForm and populate it with example dWidgets. 
		"""
		frame = ui.dForm()
		frame.Width, frame.Height = 640, 480
		frame.Caption = "Test of all the dControls"
		frame.debug = True

		panel = ui.dPanel(frame)

		labelWidth = 150
		labelAlignment = wx.ALIGN_RIGHT

		vs = wx.BoxSizer(wx.VERTICAL)

		for obj in ((ui.dTextBox(panel), "txtCounty", "ccounty"), 
					(ui.dTextBox(panel), "txtCity", "ccity"),
					(ui.dTextBox(panel), "txtZipcode", "czip"),
					(ui.dSpinner(panel), "spn1", "iid"),
					(ui.dCheckBox(panel), "chk1"),
					(ui.dEditBox(panel), "edt1"),
					(ui.dCommandButton(panel), "cmd1")):
			bs = wx.BoxSizer(wx.HORIZONTAL)
			label = ui.dLabel(panel, style=wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE)
			label.Width = labelWidth

			try:
				lblName = obj[2]
			except IndexError:
				lblName = "%s" % obj[1]
			label.Name = lblName
			label.Caption = "%s:" % lblName
			bs.Add(label)

			object = obj[0]
			if isinstance(object, ui.dEditBox):
				expandFlags = wx.EXPAND
			else:
				expandFlags = 0

			object.Name = "%s" % obj[1]
			object.debug = True # show the events

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

