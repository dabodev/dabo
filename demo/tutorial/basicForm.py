# -*- coding: utf-8 -*-
import dabo

# instantiate the application object:
app = dabo.dApp()

# instantiate the main form:
app.setup()

# instantiate a dForm as a child of the main form:
form = dabo.ui.dForm(app.MainForm, Caption="Hello, Dabo users!")

# instantiate a textbox as a child of the dForm:
tb = form.addObject(dabo.ui.dTextBox, "tbox")

# We can address the textbox directly...
tb.Value = "Cool stuff!"

# ...or in the containership hierarchy!
form.tbox.FontBold = True

# show the form:
form.Visible = True

# start the event loop:
app.start()

