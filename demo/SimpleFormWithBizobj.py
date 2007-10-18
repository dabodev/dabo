#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" SimpleFormWithBizobj.py

This demo shows a subclass of dabo.ui.dForm populated with various dControl 
instances. The dForm has a dabo.biz.dBizobj attached, which is attached to 
a dabo.db.dCursor, which handles talking to the MySQLdb backend.

Each dControl has its DataSource and DataField properties set appropriately, 
so the control's value reflects the current value in the cursor.

This is meant to be a simple example (one small script) to show one way to
build multi-tier applications in Dabo.

Requires:
	dabo
	wx  
	Database connector (one or more of the following):
		MySQLdb 
		kinterbasdb
		psycopg
		pysqlite
		MS SQL Server
	unblocked Internet connection on:
		port 3306 (for MySQL)
		or port 3050 (for Firebird)
		or port 5432 (for PostgreSQL)
		or port 1433 (for MS SQL Server)
	to dabodev.com  
	(No connection needed for SQLite, since that runs locally)

To use this example with a particular backend, uncomment that 
line below, and comment out the other types.
"""
#--------------------------------------
# Uncomment the appropriate backend name
backend = "MySQL"
#backend = "Firebird"
#backend = "PostgreSQL"
### If you use MS SQL Server, make sure to set the Host
### on line 86 below to your host, because Dabo doesn't
### offer a public server for MS SQL Server.
#backend = "MsSQL"
#backend = "SQLite"
#--------------------------------------

import os
import dabo
import dabo.db as db
import dabo.biz as biz
import dabo.ui as ui
import dabo.lib.datanav as datanav
from dabo.dLocalize import _
import dabo.dException as dException

# Dabo is a 3-tier application framework, which means that there is a 
# database tier, a business object tier, and a user-interface tier. This
# demo instantiates the Dabo application object which holds all these 
# tiers together, but before that can happen we must subclass the relevant
# base classes in each of the tiers. Follow along with the subclasses.
# We start with the database, followed by the bizobj and the ui.


# DB tier:
# There isn't much to do here except define some connection information
# parameters. When the form instantiates the bizobj, it'll first instantiate
# a dConnection object, which gets created using the connect info defined
# here.
class MyConnectInfo(db.dConnectInfo):
	def initProperties(self):
		self.DbType = backend
		self.Host = "dabodev.com"
		self.Database = "webtest"
		self.User = "webuser"
		self.Name = "SimpleDemo"
		if backend == "MySQL":
			self.Port = 3306
			self.Password = "NBDL23O83ZF4JA0E8CS04V05"  # (obscured)
		elif backend == "Firebird":
			self.Port = 3050
			self.Password = "Z35C39V79Q9EYBBJ54"  # (obscured)
		elif backend == "PostgreSQL":
			self.Port = 5432
			self.Password = "Z35C39V79Q9EYBBJ54"  # (obscured)
		elif backend == "MsSQL":
			# Make sure to change this to your server!!!
			self.Host = "192.168.0.18"
			self.Port = 1433
			self.Password = "Z35C39V79Q9EYBBJ54"  # (obscured)
		elif backend == "SQLite":
			# Only the database name is needed. Change this
			# to the path to your database file, if needed.
			self.Database = "webtest.sqlite"
			self.Host = None
			self.Port = None
			self.Password = None
		
# Bizobj tier:
# For this demo, we define only one bizobj.
class MyBizobj(biz.dBizobj):
	# This is a subclass of dabo's dBizobj base class. Look how simple it
	# is to set up the required parameters.

	def initProperties(self):
		self.DataSource = "zipcodes"     # the 'alias' for the bizobj/cursor
		self.KeyField = "iid"            # the primary key
		self.RequeryOnLoad = False       # don't do an implicit requery on init
		self.DefaultValues = {"ccity":"Penfield", "cstateprov":"NY", "czip":"14526"}


	def afterInit(self):
		# Set the default values for new records added
		self.setFromClause("zipcodes")


	def validateRecord(self):
		# Here are your business rules. We start with a pretty silly one,
		# and go from there. This is pretty easy stuff!

		# Initially set the error message to an empty string. If this method 
		# makes it all the way through with no biz rule violations, the string will
		# still be empty and the bizobj will let the commit happen.
		errorText = ""

		# Biz rules follow. These can be as complex as necessary, the key 
		# thing is to remember to add to the error message so the user knows
		# why a failure happened. You can also use the localization function
		# named _() around your text if you need to provide localized 
		# messages.

		# Rules for ccity:
		if self.Record.ccity.find("Dabo") >= 0:
			# We aren't allowing cities to be named after Dabo.
			errorText += _("Don't name your cities after Dabo. Send the authors money instead.\n")

		# Rules for czip:
		if len(self.Record.czip.strip()) < 1:
			errorText += _("Zip code may not be blank.\n")
		if len(self.Record.czip.strip()) > 5:
			errorText += _("Zip code must not be more than 5 characters long.\n")

		# Tell the bizobj if all rules passed or not. If the returned string
		# is empty, everything's fine, and the validation passes.
		return errorText
	
	
	def validateField(self, fld, val):
		"""This method is used for field-level validation. You are passed the field
		name and the potential new value, and you use that to determine if the 
		value is valid or not. If not, return any non-empty value, preferably a 
		string describing the problem with the data, and the user will not be 
		able to leave the field until they enter valid data.
		"""
		errorText = ""
		# Since this gets called for all fields, separate your code based on
		# the field name.
		if fld == "ccity":
			if val.startswith("Dabo"):
				errorText = _("Please don't name your cities after Dabo!")
#		elif fld == "czip":
#			if "666" in val:
#				errorText = _("Sorry, no evil zipcodes allowed!")
		# Note that only two fields are checked. The rest will go through
		# without problem.
		return errorText
		


# UI tier:

# First, we've got to tell Dabo which UI library to use. There are various ways of
# doing this:
#
#	+ dabo.ui.loadUI("<uiName>")
#
#	+ app.UI = "<uiName>"
#
#   + Setting the DABO_DEFAULT_UI environmental variable
#
#   + When dApp instantiates, if the UI library hasn't been loaded yet, it will 
#	default to "wx". However, this will usually be too late: your own UI class
#	definitions will already be loaded. In this demo, for example, the Application
#	isn't instantiated until the end of this script.
#
# However you do it, you must set the UI lib before any Dabo-based class definitions 
# are made, or errors will occur.
dabo.ui.loadUI("wx")

# Now, we define the field specifications. Normally, you'd put this in a separate
# file on disk, but we wanted to keep this demo simple and single-file, so you can
# easily follow along. Use the FieldSpecEditor to graphically edit your spec files,
# and use the appWizard to generate initial versions of them. 
fsXML = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<daboAppSpecs>
	<table name="zipcodes">
		<fields>
			<field name="czip" type="char" caption="Zip Code" 
				searchInclude="1" searchOrder="0" wordSearch="0"
				listInclude="1" listColWidth="100" listOrder="0"
				editInclude="1" editReadOnly="0" editOrder="0"  />
			<field name="ctimezonediff" type="char" caption="Time Zone Difference" 
				searchInclude="0" searchOrder="10" wordSearch="0"
				listInclude="0" listColWidth="100" listOrder="10"
				editInclude="1" editReadOnly="0" editOrder="10"  />
			<field name="cstateprov" type="char" caption="State / Province" 
				searchInclude="1" searchOrder="20" wordSearch="0"
				listInclude="1" listColWidth="100" listOrder="20"
				editInclude="1" editReadOnly="0" editOrder="20"  />
			<field name="ccity" type="char" caption="City" 
				searchInclude="1" searchOrder="30" wordSearch="0"
				listInclude="1" listColWidth="100" listOrder="30"
				editInclude="1" editReadOnly="0" editOrder="30"  />
			<field name="iid" type="int" caption="iid" 
				searchInclude="0" searchOrder="40" wordSearch="0"
				listInclude="0" listColWidth="100" listOrder="40"
				editInclude="1" editReadOnly="0" editOrder="999"  />
			<field name="clongitude" type="char" caption="Longitude" 
				searchInclude="1" searchOrder="50" wordSearch="0"
				listInclude="0" listColWidth="100" listOrder="50"
				editInclude="1" editReadOnly="0" editOrder="50"  />
			<field name="ccounty" type="char" caption="County" 
				searchInclude="1" searchOrder="60" wordSearch="0"
				listInclude="1" listColWidth="100" listOrder="60"
				editInclude="1" editReadOnly="0" editOrder="60"  />
			<field name="clatitude" type="char" caption="Latitude" 
				searchInclude="1" searchOrder="70" wordSearch="0"
				listInclude="0" listColWidth="100" listOrder="70"
				editInclude="1" editReadOnly="0" editOrder="70"  />
			<field name="careacode" type="char" caption="Area Code" 
				searchInclude="1" searchOrder="80" wordSearch="0"
				listInclude="0" listColWidth="100" listOrder="80"
				editInclude="1" editReadOnly="0" editOrder="80"  />
		</fields>
	</table>

</daboAppSpecs>
"""


# We subclass dabo.lib.datanav.Form, which is a plain dForm with added
# data navigation abilities.
class MyForm(datanav.Form):
	def initProperties(self):
		self.Name = "MyForm"
		self.Caption = "Zip Codes"
		self.Size = (500, 540)
		self.Position = (40, 60)
		# Try the various pageframe styles by uncommenting
		# the appropriate line for each style and run the demo
		self.pageFrameStyle = "tabs"  # Default
		#self.pageFrameStyle = "list"
		#self.pageFrameStyle = "select"
		
		# You can also experiment with different positions for 
		# the page selection controls. 
		self.tabPosition = "Top"		# Default
		#self.tabPosition = "Bottom"
		#self.tabPosition = "Left"
		#self.tabPosition = "Right"
		
		

	def afterInit(self):
		MyForm.doDefault()
		ci = MyConnectInfo()
		# Send the connection info to the Application object
		self.Application.addConnectInfo(ci)
		# Ask for the connection by name.
		self.connection = self.Application.getConnectionByName("SimpleDemo")
		self.instantiateBizobj()        

		# Set up the field information for the form from the xml previously
		# defined.
		self.setFieldSpecs(fsXML, "zipcodes")
		# The form now knows what it needs to create itself. Do it!
		self.creation()
		
	def instantiateBizobj(self):
		self.addBizobj(MyBizobj(self.connection))
		
		
def main():
	app = dabo.dApp()  # Instantiate the application object
	app.BasePrefKey = "demo.simpleFormWithBizobj"
	app.DatabaseActivityLog = "DB"
	app.MainFormClass = MyForm  # Make our form the app's main form
	app.start()  # start the app event loop


# The code below will only get executed if this file is run as a script
# versus imported as a module. This is how this demo is meant to be run,
# but remember this Python 'feature' when developing your own subclasses:
# it is great for setting up simple unit tests.
if __name__ == "__main__":
	main()
