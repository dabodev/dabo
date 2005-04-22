""" 
	dApp.py : The application object for Dabo.

	This object gets instantiated from the client app's main.py,
	and lives through the life of the application.

		-- set up an empty data connections object which holds 
		-- connectInfo objects connected to pretty names. If there 
		-- is a file named 'default.cnxml' present, it will import the
		-- connection definitions contained in that. If no file of that
		-- name exists, it will import any .cnxml file it finds. If there
		-- are no such files, it will then revert to the old behavior
		-- of importing a file in the current directory called 
		-- 'dbConnectionDefs.py', which contains connection
		-- definitions in python code format instead of XML.

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
import sys, os, warnings, glob
import ConfigParser
import dabo, dabo.ui, dabo.db
import dabo.common, dSecurityManager
from dLocalize import _
from dabo.common.SimpleCrypt import SimpleCrypt


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
		try:
			index = self.index(objRef)
		except ValueError:
			index = None
		if index is not None:
			del self[index]


class dApp(dabo.common.dObject):
	""" dabo.dApp

		The containing object for the entire application.
		Various UI's will have app objects also, which 
		dabo.App is a wrapper for. 
	"""
	def __init__(self):
		self._uiAlreadySet = False
		dabo.dAppRef = self
		#dApp.doDefault()
		super(dApp, self).__init__()
		self._initProperties()
		# egl: added the option of keeping the main form hidden
		# initially. The default behavior is for it to be shown, as usual.
		self.showMainFormOnStart = True
		self._wasSetup = False
		self._cryptoProvider = None
		

	def setup(self, initUI=True):
		""" Set up the app - call this before start()."""

		# dabo is going to want to import various things from the Home Directory
		if self.HomeDirectory not in sys.path:
			sys.path.append(self.HomeDirectory)

		if not self.getAppInfo("appName"):
			self.setAppInfo("appName", "Dabo")
		if not self.getAppInfo("appVersion"):
			self.setAppInfo("appVersion", dabo.version["version"])
		if not self.getAppInfo("vendorName"):
			self.setAppInfo("vendorName", "Dabo")

		self._initDB()
		
		if initUI:
			self._initUI()

			self.uiApp = dabo.ui.uiApp()
			self.uiApp.setup(self)
		else:
			self.uiApp = None
		# Flip the flag
		self._wasSetup = True

	
	def start(self):
		""" 
		Start the application event loop, which involves
			wrapping the application object for the ui library
			being used.
		"""
		if not self._wasSetup:
			# Convenience; if you don't need to customize setup(), just
			# call start()
			self.setup()
			
		if (not self.SecurityManager or not self.SecurityManager.RequireAppLogin
			or self.SecurityManager.login()):
			
			userName = self.getUserCaption()
			if userName:
				userName = " (%s)" % userName
			else:
				userName = ""
				
			self.uiApp.start(self)
		self.finish()


	def finish(self):
		""" 
		The main event loop has exited and the application
			is about to finish.
		"""
		self.uiApp.finish()
		dabo.infoLog.write(_("Application finished."))
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


	def getUserSettingKeys(self, spec):
		"""Return a list of all keys underneath <spec>.
		
		For example, if spec is "appWizard.dbDefaults", and there are
		userSettings entries for:
			appWizard.dbDefaults.pkm.Host
			appWizard.dbDefaults.pkm.User
			appWizard.dbDefaults.egl.Host
			
		The return value would be ["pkm", "egl"]
		"""
		configFileName = "%s/.userSettings.ini" % self.HomeDirectory

		cp = ConfigParser.ConfigParser()
		cp.read(configFileName)

		spec = spec.lower()
		
		try:
			items = cp.items("UserSettings")
		except ConfigParser.NoSectionError:
			items = []
		
		ret = []	
		for item in items:
			wholekey = item[0].lower()
			if wholekey[:len(spec)] == spec:
				key = wholekey[len(spec):].split(".")[0]
				if ret.count(key) == 0:
					ret.append(key)
		return ret
		
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
		configFileName = "%s/.userSettings.ini" % self.HomeDirectory

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


	def setUserSetting(self, item, value):
		"""Persist a value to the user settings file.
		"""
		# For now, save this info in a plain ini file. Eventually, I'd like
		# to see this get saved in a persistent dabosettings db table.
		configFileName = "%s/.userSettings.ini" % self.HomeDirectory

		cp = ConfigParser.ConfigParser()
		cp.read(configFileName)

		if type(value) in (str, unicode):
			valueType = "C"
		elif type(value) == bool:
			valueType = "L"
		elif type(value) in (float,):
			valueType = "N"
		elif type(value) in (int, long):
			valueType = "I"
			
		if not cp.has_section("UserSettings"):
			cp.add_section("UserSettings")
		cp.set("UserSettings", item, str(value))

		if not cp.has_section("UserSettingsValueTypes"):
			cp.add_section("UserSettingsValueTypes")
		cp.set("UserSettingsValueTypes", item, valueType)

		configFile = open(configFileName, "w")
		cp.write(configFile)
		configFile.close()
		
		
	def getUserCaption(self):
		""" Return the full name of the currently logged-on user.
		"""
		if self.SecurityManager:
			return self.SecurityManager.UserCaption
		else:
			return None
			

	# These two methods pass encryption/decryption requests
	# to the Crypto object
	def encrypt(self, val):
		return self.Crypto.encrypt(val)
	def decrypt(self, val):
		return self.Crypto.decrypt(val)

	
	def getCharset(self):
		"""Are we running a unicode-capable UI? Returns 
		'unicode' or 'ascii'.
		"""
		return self.uiApp.charset
		
		
	def _initProperties(self):
		""" Initialize the public properties of the app object. """

		self.uiType   = None    # ("wx", "qt", "curses", "http", etc.)
		#self.uiModule = None

		# Initialize UI collections
		self.uiForms = Collection()
		self.uiMenus = Collection()
		self.uiToolBars = Collection()
		self.uiResources = {}

		# Initialize DB collections
		self.dbConnectionDefs = {} 

		self._appInfo = {}

	def _initDB(self):
		"""Set the available connection definitions for use by the app. 
		First look for a file named 'default.cnxml'; if none exists, 
		read in all .cnxml files. If no such XML definition files exist,
		check for a python code definition file named 'dbConnectionDefs'.
		"""
		connDefs = {}
		parser = dabo.common.connParser
		homeDir = self.HomeDirectory
		if os.path.exists("%sdefault.cnxml" % homeDir):
			connDefs = parser.importConnections("%sdefault.cnxml" % homeDir)
		if not connDefs:
			# Try importing all .cnxml files
			cnFiles = glob.glob("*.cnxml")
			for cn in cnFiles:
				cnDefs = parser.importConnections(cn)
				connDefs.update(cnDefs)
		if not connDefs:
			# No XML definitions present. Try looking for python code
			# definitions instead.
			try:
				import dbConnectionDefs
				connDefs = dbConnectionDefs.getDefs()
			except:
				pass
		
		if connDefs:
			# For each connection definition, add an entry to 
			# self.dbConnectionDefs that contains a key on the 
			# name, and a value of a dConnectInfo object.
			for k in connDefs.keys():
				entry = connDefs[k]
				ci = dabo.db.dConnectInfo()
				ci.setConnInfo(entry)
				self.dbConnectionDefs[k] = ci

			dabo.infoLog.write(_("%s database connection definition(s) loaded.") % (
												len(self.dbConnectionDefs)))

		else:
			dabo.infoLog.write(_("No database connection definitions loaded (dbConnectionDefs.py)"))


	def _initUI(self):
		""" Set the user-interface library for the application. 
		
		Ignored if the UI was already explicitly set by user code.
		"""
		if self.UI is None and not self._uiAlreadySet:
			# For now, default to wx, but it should be enhanced to read an
			# application config file. Actually, that may not be necessary, as the
			# user's main.py can just set the UI directly now: dApp.UI = "qt".
			self.UI = "wx"
		else:
			# Custom app code or the dabo.ui module already set this: don't touch
			dabo.infoLog.write(_("User interface already set to '%s', so dApp didn't "
				" touch it." % (self.UI,)))

	
	########################
	# This next section simply passes menu events to the UI
	# layer to be handled there.
	def onCmdWin(self, evt):
		self.uiApp.onCmdWin(evt)
	def onWinClose(self, evt):
		self.uiApp.onWinClose(evt)
	def onFileExit(self, evt):
		self.uiApp.onFileExit(evt)
	def onEditUndo(self, evt):
		self.uiApp.onEditUndo(evt)
	def onEditRedo(self, evt):
		self.uiApp.onEditRedo(evt)
	def onEditCut(self, evt):
		self.uiApp.onEditCut(evt)
	def onEditCopy(self, evt):
		self.uiApp.onEditCopy(evt)
	def onEditPaste(self, evt):
		self.uiApp.onEditPaste(evt)
	def onEditFind(self, evt):
		self.uiApp.onEditFind(evt)
	def onEditFindAgain(self, evt):
		self.uiApp.onEditFindAgain(evt)
	def onEditPreferences(self, evt):
		self.uiApp.onEditPreferences(evt)
	############################	
	
	
	def copyToClipboard(self, txt):
		self.uiApp.copyToClipboard(txt)
		
	def onHelpAbout(self, evt):
		import dabo.ui.dialogs.about as about
		dlg = about.About(self.MainForm)
		dlg.show()
	
	def _getHomeDirectory(self):
		try:
			hd = self._homeDirectory
		except AttributeError:
			# Note: sometimes the runtime distros will alter the path so
			# that the first entry is not a valid directory. Go through the path
			# and use the first valid directory.
			hd = None
			for pth in sys.path:
				if os.path.exists(os.path.join(pth, ".")):
					hd = pth
					break
			if hd is None:
				# punt:
				hd = os.getcwd()
			self._homeDirectory = hd
			
		return hd
		
	def _setHomeDirectory(self, val):
		self._homeDirectory = val

				
	def _getMainForm(self):
		try:
			f = self._mainForm
		except AttributeError:
			f = None
			self._mainForm = None
		return f
			
	def _setMainForm(self, val):
		self._mainForm = val

				
	def _getMainFormClass(self):
		try:
			c = self._mainFormClass
		except AttributeError:
			c = dabo.ui.dFormMain
			self._mainFormClass = c
		return c
			
	def _setMainFormClass(self, val):
		self._mainFormClass = val
		
		
	def _getSecurityManager(self):
		try:
			return self._securityManager
		except AttributeError:
			return None
			
	def _setSecurityManager(self, value):
		if isinstance(value, dSecurityManager.dSecurityManager):
			if self.SecurityManager:
				warnings.warn(Warning, _("SecurityManager previously set"))
			self._securityManager = value
		else:
			raise TypeError, _("SecurityManager must descend from dSecurityManager.")
			
			
	def _getUI(self):
		try:
			return dabo.ui.getUIType()
		except AttributeError:
			return None
			
	def _setUI(self, uiType):
		# Load the appropriate ui module. dabo.ui will now contain
		# the classes of that library, wx for instance.
		if self.UI is None:
			if dabo.ui.loadUI(uiType):
				self._uiAlreadySet = True
				dabo.infoLog.write(_("User interface set to '%s' by dApp.") % (uiType,))
			else:
				dabo.infoLog.write(_("Tried to set UI to '%s', but it failed." % (uiType,)))
		else:
			raise RuntimeError, _("The UI cannot be reset once assigned.")

	def _getPlatform(self):
		return self.uiApp._getPlatform()


	def _getActiveForm(self):
		if self.uiApp is not None:
			return self.uiApp.ActiveForm
		else:
			return None
			
	def _setActiveForm(self, frm):
		if self.uiApp is not None:
			self.uiApp._setActiveForm(frm)
		else:
			dabo.errorLog.write("Can't set ActiveForm: no uiApp.")
	
	
	def _getCrypto(self):
		if self._cryptoProvider is None:
			# Use the default crypto
			self._cryptoProvider = SimpleCrypt()
		return self._cryptoProvider
	def _setCrypto(self, val):
		self._cryptoProvider = val

	
	ActiveForm = property(_getActiveForm, None, None, 
			_("Returns the form that currently has focus, or None.  (dForm)" ) )
	
	Crypto = property(_getCrypto, _setCrypto, None, 
			_("Reference to the object that provides cryptographic services.  (varies)" ) )
	
	HomeDirectory = property(_getHomeDirectory, _setHomeDirectory, None,
			_("Specifies the home-base directory for the application's program files."))
		
	MainForm = property(_getMainForm, _setMainForm, None,
			_("""The object reference to the main form of the application, or None. 
			This gets set automatically during application setup, based on the 
			MainFormClass."""))
		
	MainFormClass = property(_getMainFormClass, _setMainFormClass, None,
			_("""Specifies the class to use to instantiate the main form. Defaults to 
			the dFormMain base class. Set to None if you don't want a main form."""))
	
	Platform = property(_getPlatform, None, None,
			_("""Returns one of 'Mac', 'Win' or 'GTK', depending on where we're 
			running  (string)""") )
			
	UI = property(_getUI, _setUI, None, 
			_("""Specifies the user interface to load, or None. Once set, 
			it cannot be reassigned.  (str)""") )
	
	SecurityManager = property(_getSecurityManager, _setSecurityManager, None, 
			_("""Specifies the Security Manager, if any. You must subclass 
			dSecurityManager, overriding the appropriate hooks and properties, 
			and then set dApp.SecurityManager to an instance of your subclass. 
			There is no security manager by default - you explicitly set this 
			to use Dabo security.""") )

