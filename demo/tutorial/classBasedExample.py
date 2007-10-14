# -*- coding: utf-8 -*-
import dabo

# Instantiate an application object, and tell it to load the wx
# ui library. It is necessary to load a ui library prior to 
# defining any subclasses of ui controls. This is one way to
# accomplish this. Note that the loading of a particular UI
# can happen at most once, so this will likely be the very first
# thing your application does. 
app = dabo.dApp(UI="wx")


# Define a couple subclasses, a textbox and a form. Note that
# for this simple case, it would have been easier just to instantiate
# Dabo classes, instead of subclassing. See basicForm.py for an 
# example using instances.
class MyTextBox(dabo.ui.dTextBox):
	def initProperties(self):
		self.Width = 200
		self.Value = "Planet Earth is blue"

class MyForm(dabo.ui.dForm):
	def afterInit(self):
		self.addObject(MyTextBox)
	def initProperties(self):
		self.Caption = "Ground Control To Major Tom"

# Tell the application object to use our custom form as the main
# form of the application (the application object will handle 
# instantiating the form, but see basicForm.py if you want to see
# how to instantiate it manually by yourself:
app.MainFormClass = MyForm

# Start the event loop:
app.start()

