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

	def runTest(self, classRefs, *args, **kwargs):
		if type(classRefs) not in (tuple, list):
			classRefs = (classRefs,)
		if issubclass(classRefs[0], wx.Frame):
			# Can't display a frame within another frame, so create this
			# class as the main frame
			frame = classRefs[0](None, *args, **kwargs)
		else:
			frame = wx.Frame(None, -1, "")
			frame.SetSizer(ui.dSizer("Vertical"))
			for class_ in classRefs:
				object = class_(frame, LogEvents=logEvents, *args, **kwargs)
				object.Width = 300
				frame.GetSizer().append(object, 1, "expand")
			
			# This will get a good approximation of the required size
			w,h = frame.GetSizer().GetMinSize()
			# Some controls don't report sizing correctly, so set a minimum
			w = max(w, 100)
			h = max(h, 50)
			print "SZ", w, h
			
			frame.SetSize( (w+10, h+30) )
			if len(classRefs) > 1:
				frame.SetLabel("Test of multiple objects")
			else:
				frame.SetLabel("Test of %s" % object.BaseClass.__name__)
			object.SetFocus()
		
		frame.Show()
		frame.Layout()
		#object.Show()
		self.app.MainLoop()

	def testAll(self):
		""" Create a dForm and populate it with example dWidgets. 
		"""
		frame = ui.dForm(Name="formTest")
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
			label = ui.dLabel(panel, Alignment="Right", AutoResize=False, Width=labelWidth)

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

