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

Dabo is fun to say, which is enough justification for its name, but 
perhaps it could stand for:
	Database Application Business Objects
	Database Application Builder O (Just think, it could have been ActiveO... <g>)
	Object oriented Business Application Development (but OBAD sounds so bad)

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
	+ Python 2.3 or higher

	+ wxPython 2.5 or higher, which has a dependency on:
		+ wxWindows 2.5 or higher
		(only necessary for apps with a ui: because of the modular
		nature of Dabo's design, it is possible to use just the
		db layer, or the db layer in conjunction with the biz
		layer, with no ui at all.)

	+ Windows 98SE or higher
	+ Macintosh OSX 10.2 or higher
	+ Linux 2.4 with X11 running

	+ Access to some sort of database server, along with the 
	appropriate Python driver(s) installed. For example, for
	MySQL you'll need to have the MySQL client libraries
	installed, as well as the MySQLDb Python module. (Dabo
	does not use ODBC: it connects directly using the Python
	DB API coupled with the individual database drivers. This
	is, at the same time, less flexible, tougher to get started
	with, but more capable, more multi-platform, and better 
	performing, than ODBC is.) 

How you get started is pretty much up to you. Look at the demo.
Run a wizard. Hand-edit the data definition files.

ToDo: pointers to get started.

"""

# Instantiate the logger object, which will send messages to user-overridable
# locations. Do this before any other imports.
import sys
import dabo.common
infoLog = dabo.common.Log()
infoLog.Caption = "Dabo Info Log"
infoLog.LogObject = sys.stdout
errorLog = dabo.common.Log()
errorLog.Caption = "Dabo Error Log"
errorLog.LogObject = sys.stderr

from dApp import dApp
from __version__ import version
import dEvents

# dApp will change the following values upon its __init__:
dAppRef = None

# Event logging is turned off globally by default for performance reasons.
# Set to True (and also set LogEvents on the object(s)) to get logging.
eventLogging = False

# Set the following to True to get all the data in the UI event put into
# the dEvent EventData dictionary. Only do that for testing, though, 
# because it is very expensive from a performance standpoint.
allNativeEventInfo = False
