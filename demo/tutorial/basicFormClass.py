# -*- coding: utf-8 -*-
"""This is the same as basicForm.py, except that the form is defined
as a class.
"""

import dabo
# Tell Dabo to use the wxPython toolkit for its UI/
dabo.ui.loadUI("wx")


class TestForm(dabo.ui.dForm):
	def afterInit(self):
		# Set the caption
		self.Caption = "Hello, Dabo users!"

		# instantiate a textbox as a child of the dForm:
		tb = self.addObject(dabo.ui.dTextBox, "tbox")
		but = self.addObject(dabo.ui.dButton, RegID="but", Caption="Launch new form",
				Top=42, Width=150)

		# We can address the textbox directly...
		tb.Value = "Cool stuff!"

		# ...or in the containership hierarchy!
		self.tbox.FontBold = True

	def onHit_but(self, evt):
		new_frm = TestForm(self)
		new_frm.showModal()

# This is the code that will be executed when we run this file.
if __name__ == "__main__":
	# instantiate the application object:
	app = dabo.dApp()
	
	# Set the app to use the class we defined above.
	app.MainFormClass = TestForm
	
	# start the event loop:
	app.start()

