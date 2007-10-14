# -*- coding: utf-8 -*-
"""Connect to a database, execute an SQL statement, and browse the results."""

import sys
import os
from optparse import OptionParser
import dabo
from dabo.lib.SimpleCrypt import SimpleCrypt

# The SQL can get set from the command line by the user, but here's the default:
defaultSQL = """
select iid as Id,
       ctitle as Title,
       ddate as Date
  from recipes
 where recipes.ctitle like "%apple%"
 order by ctitle
"""

# When coding scripts that run from the command line, don't be tempted to
# code your own parsing of sys.argv: learn how to use the standard optparse
# package instead. The following defines the command-line interface for the
# application. We expose all the connection info as well as the SQL statement
# to execute, but provide default values to the recipes demo database if no
# command line arguments are passed.
parser = OptionParser()
parser.add_option("-t", "--type", dest="dbType", default="MySQL",
		help="Dabo database type (MySQL, PostgreSQL, etc.)", metavar="TYPE")
parser.add_option("-H", "--host", dest="host", default="paulmcnett.com",
		help="Name or host ip address of database server", metavar="HOST")
parser.add_option("-u", "--user", dest="user", default="dabo",
		help="Username to login to database", metavar="USER")
parser.add_option("-p", "--passwd", dest="passwd", default="dabo",
		help="Password (unobscured) to login to database", metavar="PASSWD")
parser.add_option("-d", "--database", dest="db", default="dabotest",
		help="Database to login to", metavar="DATABASE")
parser.add_option("-s", "--sql", dest="sql", default=defaultSQL,	
		help="SQL statement to execute", metavar="SQL")
parser.set_description(__doc__)

(options, args) = parser.parse_args()

# If the user had issued "python browseDataSet.py -h", the usage will have displayed
# and the script exited (feature of optparse). So, now that we are here, we know we
# will be doing something real.

# First thing, instantiate dApp:
app = dabo.dApp(UI="wx")

# Calling setup() on the app object is also a good idea to do right away,
# as this is where the initialization of the UI lib's application object
# occurs.
app.setup()


# Get the dabo Connection Info based on the command line args received:
ci = dabo.db.dConnectInfo(DbType=options.dbType, 
		Host=options.host, 
		User=options.user, 
		PlainTextPassword=options.passwd, 
		Database=options.db)

# Get the dabo Connection object, based on the connect info:
conn = dabo.db.dConnection(ci)

# Get a dabo Cursor object from the connection:
cur = conn.getDaboCursor()

# Execute the sql:
cur.execute(options.sql)

# Get the browse form and make it the mainform:
frm, grd = dabo.ui.browse(cur)
app.MainForm = frm

# The following is the functional equivilent of READ EVENTS in Visual FoxPro:
app.start()

