#!/usr/bin/env python
# -*- coding: utf-8 -*-

#!/usr/bin/env python

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

# Define namespaces in the Application object where the biz, db and ui 
# packages can be accessed globally:
app.db = db
app.ui = ui
app.biz = biz

app.setup()

# Set up a global connection to the database that all bizobjs will share:
app.dbConnection = app.getConnectionByName("MySQL-default")

# Show the customer form:
ui.FrmCustomer(app.MainForm).show()

# Start the application event loop:
app.start()
