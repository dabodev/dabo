# -*- coding: utf-8 -*-
""" Dabo: A Framework for developing data-driven business applications

Dabo is for developing multi-platform database business applications -
you know, applications that need to connect to a database server (MySQL,
Oracle, MS-SQL, whatever), get recordsets of data based on criteria 
set by the user, provide easy ways to edit and commit changes to the 
data, and to report on the data.

For basic, easy use that hopefully satisfies 80% of your needs, you 
simply create/edit data definition files that Dabo uses to dynamically
create things like menus, edit forms, data browsing grids, etc.

So, the basic idea is that you have a functional, working, albeit basic
application up and running very quickly, and you can then spend time 
getting all the fancy bells and whistles implemented. Keep things as 
simple as possible though, while still fulfilling your customer's 
specifications. Simplicity is the better part of elegance.

Beyond the wizards and xml definition files, Dabo exposes a nice
API in Python for manually creating your own class definitions. IOW,
we let you have as much control as you need. You aren't required to
take advantage of our xml definition formats at all.

Dabo has three main submodules, representing the three tiers common
in modern database application design:

	dabo.db  : database
	dabo.biz : business objects
	dabo.ui  : user interface

dabo.db and dabo.biz are completely ui-free, while dabo.ui (currently)
requires wxPython. We have allowed for possible future support for other
ui libraries, such as PyQt, tk, and curses.

The Dabo framework will have to be distributed to your client's machine(s),
along with your project-specific data definitions and (if applicable), your
subclasses of the Dabo classes and additional Python scripts, if any. There 
are ways to do runtime deployment via installers that take the complexity 
out of this, but that is outside the scope of Dabo itself, and you'll use
a different method for each target platform.

To run Dabo, and apps based on Dabo, you need:
	+ Python 2.3 or higher (2.5 recommended)

	+ wxPython 2.6.1.1 or higher (2.8.x highly recommended)
		(only necessary for apps with a ui: because of the modular
		nature of Dabo's design, it is possible to use just the
		db layer, or the db layer in conjunction with the biz
		layer, with no ui at all.)
	
	+ SQLite3: this is used internally for managing preferences, as 
		well as for cursor management.
	
	+	pysqlite2: The Python dbapi module for SQLite. (Not needed in 
			Python 2.5 and higher)

	+ Windows 98SE or higher
	+ Macintosh OSX 10.2 or higher (*much* nicer in Tiger - 10.4)
	+ Linux 2.4 with X11 running and Gtk2

	+ Access to some sort of database server, along with the 
	appropriate Python driver(s) installed. For example, for
	MySQL you'll need to have the MySQL client libraries
	installed, as well as the MySQLDb Python module. (Dabo
	does not use ODBC: it connects directly using the Python
	DB API coupled with the individual database drivers. This
	is, at the same time, less flexible, tougher to get started
	with, but more capable, more multi-platform, and better 
	performing, than ODBC is.) (we recommend starting with MySQL
	installed, because all of the demo code has the best support
	for MySQL).

How you get started is pretty much up to you. Look at the code in the
separate dabodemo project. Run the AppWizard in the separate daboide
project. Hand-edit the data definition files and Python code that the 
AppWizard generates for you.

For some quick eye-candy, once you've installed Dabo using the standard
'python setup.py install' method, do this from your Python interpreter:

	import dabo
	dabo.dApp().start()

press Ctrl+D and type the following into the command window that appears:

	tb = self.addObject(dabo.ui.dTextBox)

Notice the textbox in the upper left hand corner?

	tb.Value = "yippee!"
	tb.FontBold = True
	print tb.Value

Now, use the ui to change the value in the textbox, and switch back to
the command window.

	print tb.Value

Have fun in your exploration of Dabo! 
"""

import os
import sys
try:
	import pysqlite2
except ImportError:
	try:
		import sqlite3
	except ImportError:
		msg = """

Dabo requires SQLite 3 and the pysqlite2 module. You will have to install these
free products before running Dabo. You can get them from the following locations:

SQLite: http://www.sqlite.org/download.html
pysqlite2: http://initd.org/tracker/pysqlite

"""	
		sys.exit(msg)

# dApp will change the following values upon its __init__:
dAppRef = None

# Install localization service for dabo. dApp will install localization service
# for the user application separately.
import dLocalize
dLocalize.install("dabo")


# Instantiate the logger object, which will send messages to user-overridable
# locations. Do this before any other imports.
from dabo.lib.logger import Log
infoLog = Log()
infoLog.Caption = "Dabo Info Log"
infoLog.LogObject = sys.stdout
errorLog = Log()
errorLog.Caption = "Dabo Error Log"
errorLog.LogObject = sys.stderr
# Create a separate log reference for event tracking.
eventLog = Log()
eventLog.Caption = "Dabo Event Log"
eventLog.LogObject = sys.stdout
# This log is set to None by default. It must be manually activated 
# via the Application object.
dbActivityLog = Log()
dbActivityLog.Caption = "Database Activity Log"
dbActivityLog.LogObject = None

# Import global settings (do this first, as other imports may rely on it):
from settings import *

from __version__ import version
import dColors
import dEvents

from dBug import logPoint
import pdb
trace = pdb.set_trace

from dApp import dApp
from dPref import dPref

# Make sure dabo.db, dabo.biz, and dabo.ui are imported:
import dabo.db
import dabo.biz
import dabo.ui

# Store the base path to the framework
frameworkPath = os.path.dirname(dabo.__file__)

# Define the standard Dabo subdirectory stucture for apps.
def _getAppDirectoryNames():
	return ("biz", "db", "ui", "resources", "reports")
	
	
# Method to create a standard Dabo directory structure layout
def makeDaboDirectories(homedir=None):
	"""If homedir is passed, the directories will be created off of that
	directory. Otherwise, it is assumed that they should be created
	in the current directory location.
	"""
	currLoc = os.getcwd()
	if homedir is not None:
		os.chdir(homedir)
	for d in _getAppDirectoryNames():
		if not os.path.exists(d):
			os.mkdir(d)
	os.chdir(currLoc)


def quickStart(homedir=None):
	"""This creates a bare-bones application in either the specified 
	directory, or the current one if none is specified.
	"""
	currLoc = os.getcwd()
	if homedir is not None:
		if not os.path.exists(homedir):
			os.makedirs(homedir)
		os.chdir(homedir)
	makeDaboDirectories()
	open("main.py", "w").write("""#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")

app = dabo.dApp()

# IMPORTANT! Change app.MainFormClass value to the name
# of the form class that you want to run when your
# application starts up.
app.MainFormClass = dabo.ui.dFormMain

app.start()
""")

	template = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
######
# In order for Dabo to 'see' classes in your %(dd)s directory, add an 
# import statement here for each class. E.g., if you have a file named
# 'MyClasses.py' in this directory, and it defines two classes named 'FirstClass'
# and 'SecondClass', add these lines:
# 
# from MyClass import FirstClass
# from MyClass import SecondClass
# 
# Now you can refer to these classes as: self.Application.%(dd)s.FirstClass and
# self.Application.%(dd)s.SecondClass
######

"""
	for dd in dabo._getAppDirectoryNames():
		fname = "%s/__init__.py" % dd
		txt = template % locals()
		open(fname, "w").write(txt)
	os.chmod("main.py", 0744)
	os.chdir(currLoc)
