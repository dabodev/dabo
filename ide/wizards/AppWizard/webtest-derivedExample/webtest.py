#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import dabo

if sys.platform[:3] == "win":
	dabo.settings.MDI = True

from App import App
import db
import biz
import ui

app = App()

# If we are running frozen, let's reroute the errorLog:
if hasattr(sys, "frozen"):
	dabo.errorLog.Caption = ""
	dabo.errorLog.LogObject = open(os.path.join(app.HomeDirectory, 
			"error.log"), "a")

# Make it easy to find any images or other files you put in the resources
# directory.
sys.path.append(os.path.join(app.HomeDirectory, "resources"))

# Define namespaces in the Application object where the biz, db and ui 
# packages can be accessed globally:
app.db = db
app.ui = ui
app.biz = biz

app.setup()

# Set up a global connection to the database that all bizobjs will share:
app.dbConnection = app.getConnectionByName("ConnectionName")

# Open one of the defined forms:
frm = ui.FrmCustomer(app.MainForm)
frm.show()

# Start the application event loop:
app.start()
