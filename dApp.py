""" 
	dApp.py : The application object for Dabo.

	This object gets instantiated from the client app's main.py,
	and lives through the life of the application.

		-- set up an empty data connections object which holds 
		-- connectInfo objects connected to pretty names. Entries
		-- can be added programatically, but upon initialiazation
		-- it will look for a file called 'dbConnectionDefs.py' which
		-- contains connection definitions.

		-- Set up a DB Connection manager, that is basically a dictionary
		-- of dConnection objects. This allows connections to be shared
		-- application-wide.

		-- decide which ui to use (wx) and gets that ball rolling

		-- make a system menu bar, based on a combination
		-- of dabo defaults and user resource files.

		-- ditto for toolbar(s)

		-- look for a mainFrame ui resource file in an expected 
		-- place, otherwise uses default dabo mainFrame, and 
		-- instantiate that. 

		-- maintain a forms collection and provide interfaces for
		-- opening dForms, closing them, and iterating through them.

		-- start the main app event loop.

		-- clean up and exit gracefully
"""
import sys, os
import ui
from biz import *
from db import *

class Collection(list):
	""" 
	Collection : Base class for the various collection
					classes used in the app object.
	"""

	def __init__(self):
		list.__init__(self)

	def add(self, objRef):
		""" 
		Collection.add(objRef)
			Add the object reference to the collection.
		"""
		self.append(objRef)

	def remove(self, objRef):
		""" 
		Collection.remove(objRef)
			Delete the object reference from the collection.
		"""
		index = self.index(objRef)

		if index >= 0:
			del self[index]


class dApp(object):
	""" dabo.dApp

		The containing object for the entire application.
		Various UI's will have app objects also, which 
		dabo.App is a wrapper for. 
	"""
	def __init__(self):
		object.__init__(self)
		self._initProperties()

	def setup(self):
		""" Set up the app - call this before start()."""

		# dabo is going to want to import various things from the homeDir
		sys.path.append(self.homeDir)

		# Init some appInfo properties:
		self.setAppInfo("appName", "Dabo")
		self.setAppInfo("appVersion", "0.1")
		self.setAppInfo("vendorName", "")

		self._initUI()
		self._initDB()

		self.uiApp = self.uiModule.uiApp()

		self.actionList.setAction("FileExit", self.uiApp.onFileExit)
		self.actionList.setAction("HelpAbout", self.uiApp.onHelpAbout)
		self.actionList.setAction("EditPreferences", self.uiApp.onEditPreferences)
		self.actionList.setAction("EditCut", self.uiApp.onEditCut)
		self.actionList.setAction("EditCopy", self.uiApp.onEditCopy)
		self.actionList.setAction("EditPaste", self.uiApp.onEditPaste)
		self.actionList.setAction("EditFind", self.uiApp.onEditFind)

		self.uiApp.setup(self)
		self.mainFrame = self.uiApp.mainFrame


	def start(self):
		""" 
		Start the application event loop, which involves
			wrapping the application object for the ui library
			being used.
		"""
		if not self.getAppInfo("appName"):
			self.setAppInfo("appName", "Dabo")
		if not self.getAppInfo("appVersion"):
			self.setAppInfo("appVersion", "0.1")
		self.uiApp.start(self)
		self.finish()


	def finish(self):
		""" 
		The main event loop has exited and the application
			is about to finish.
		"""
		print "Application finished."
		pass


	def getAppInfo(self, item):
		""" dApp.getAppInfo(self, item) -> value

			Look up the item, and return the value.
		"""
		try:
			retVal = self._appInfo[item]
		except KeyError:
			retVal = None
		return retVal


	def setAppInfo(self, item, value):
		""" dApp.getAppInfo(self, item, value) -> None

			Set item to value in the appinfo table.
		"""
		self._appInfo[item] = value


	def getUserSetting(self, item, user="*", system="*"):
		""" Return the value of the user settings table that 
			corresponds to the item, user, and system id 
			passed. Based on the ctype field in the table, 
			convert the return value into the appropriate
			type first.

			Types:    I: Int
					N: Float
					C: String
					M: String
					D: Date, saved as a string 3-tuple 
						of integers '(year,month,day)'
					T: DateTime, saved as a string 
						9-tuple of integers '(year,month,
						day,hour,minute,second,?,?,?)'

		"""
		import ConfigParser

		configFileName = '%s/.userSettings.ini' % self.homeDir

		cp = ConfigParser.ConfigParser()
		cp.read(configFileName)

		try:
			valueType = cp.get("UserSettingsValueTypes", item)
		except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
			valueType = "C"

		try:
			if valueType == "I":
				value = cp.getint("UserSettings", item)
			elif valueType == "N":
				value = cp.getfloat("UserSettings", item)
			elif valueType == "L":
				value = cp.getboolean("UserSettings", item)
			else:
				value = cp.get("UserSettings", item)
		except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
			value = None

		return value


	def setUserSetting(self, item, valueType, value, user="*", system="*"):
		""" Set the value of the user settings table that corresponds to the
			item, user, and systemid passed. If it doesn't exist in the table,
			add it. See self.getUserSetting() for the type codes. 
		"""
		# For now, save this info in a plain ini file. Eventually, I'd like
		# to see this get saved in a persistent dabosettings db table.
		import ConfigParser

		configFileName = '%s/.userSettings.ini' % self.homeDir

		cp = ConfigParser.ConfigParser()
		cp.read(configFileName)

		# convert value to string type for saving to db:
		value = str(value)

		if not cp.has_section("UserSettings"):
			cp.add_section("UserSettings")
		cp.set("UserSettings", item, value)

		if not cp.has_section("UserSettingsValueTypes"):
			cp.add_section("UserSettingsValueTypes")
		cp.set("UserSettingsValueTypes", item, valueType)

		configFile = open(configFileName, 'w')
		cp.write(configFile)
		configFile.close()

	def _initProperties(self):
		""" Initialize the public properties of the app object. """

		# it is useful to know from where we came
		self.homeDir = sys.path[0]

		self.uiType   = None    # ('wx', 'qt', 'curses', 'http', etc.)
		self.uiModule = None

		# Initialize UI collections
		self.uiForms = Collection()
		self.uiMenus = Collection()
		self.uiToolBars = Collection()
		self.uiResources = {}

		self.actionList = ui.dActionList()

		# Initialize DB collections
		self.dbConnectionDefs = {} 

		self._appInfo = {}

	def _initDB(self):
		""" Set the available connection definitions for use by the app. """

		dbConnectionDefs = None
		try:
			globals_ = {}
			execfile("%s/dbConnectionDefs.py" % (self.homeDir,), globals_)
			dbConnectionDefs = globals_["dbConnectionDefs"]
		except:
			dbConnectionDefs = None

		if dbConnectionDefs and type(dbConnectionDefs) == type(dict()):
			# For each connection definition, add an entry to 
			# self.dbConnectionDefs that contains a key on the 
			# name, and a value of a dConnectInfo object.
			for entry in dbConnectionDefs:
				try:             dbType   = dbConnectionDefs[entry]['dbType']
				except KeyError: dbType   = None
				try:             host     = dbConnectionDefs[entry]['host']
				except KeyError: host     = None
				try:             user     = dbConnectionDefs[entry]['user']
				except KeyError: user     = None
				try:             password = dbConnectionDefs[entry]['password']
				except KeyError: password = None
				try:             dbName   = dbConnectionDefs[entry]['dbName']
				except KeyError: dbName   = None
				try:             port     = dbConnectionDefs[entry]['port']
				except KeyError: port     = None

				self.dbConnectionDefs[entry] = dConnectInfo(backendName=dbType,
															host=host, 
															user=user,
															password=password,
															dbName=dbName,
															port=port)

			print "%s database connection definition(s) loaded." % (
												len(self.dbConnectionDefs))

		else:
			print "No database connection definitions loaded (dbConnectionDefs.py)"


	def _initUI(self):
		""" Set the user-interface library for the application. """

		if self.uiType == None:
			# Future: read a config file in the homeDir
			# Present: set UI to wx
			uiType = "wx"

			# Now, get the appropriate ui module into self.uiModule
			uiModule = ui.getUI(uiType)
			if uiModule != None:
				self.uiType = uiType
				self.uiModule = uiModule
		else:
			# Custom app code already set this: don't touch
			pass

		print "User interface set to %s using module %s" % (self.uiType, self.uiModule)


