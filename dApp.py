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
from dabo.lib.connParser import importConnections
import dSecurityManager
from dLocalize import _
from dabo.lib.SimpleCrypt import SimpleCrypt
from dabo.dObject import dObject
import dUserSettingProvider


class Collection(list):
	""" Collection : Base class for the various collection
	classes used in the app object.
	"""

	def __init__(self):
		list.__init__(self)


	def add(self, objRef):
		"""Add the object reference to the collection."""
		self.append(objRef)
		

	def remove(self, objRef):
		"""Delete the object reference from the collection."""
		try:
			index = self.index(objRef)
		except ValueError:
			index = None
		if index is not None:
			del self[index]


class dApp(dObject):
	"""The containing object for the entire application.

	All Dabo objects have an Application property which refers to the dApp
	instance. Instantiate your dApp object from your main script, like so:

	>>> import dabo
	>>> app = dabo.dApp
	>>> app.start()
	"""
	_call_beforeInit, _call_afterInit, _call_initProperties = False, False, True
	# Behaviors which are normal in the framework may need to
	# be modified when run as the Designer. This flag will 
	# distinguish between the two states.
	isDesigner = False
	

	def __init__(self, selfStart=False, properties=None, *args, **kwargs):
		self._uiAlreadySet = False
		dabo.dAppRef = self
		self._beforeInit()
		# If we are displaying a splash screen, these attributes control
		# its appearance. Extract them before the super call.
		self.showSplashScreen = self._extractKey(kwargs, "showSplashScreen", False)
		basepath = os.path.split(dabo.__file__)[0]
		img = os.path.join(basepath, "icons", "daboSplashName.png")
		self.splashImage = self._extractKey(kwargs, "splashImage", img)
		self.splashMaskColor = self._extractKey(kwargs, "splashMaskColor", None)
		self.splashTimeout = self._extractKey(kwargs, "splashTimeout", 5000)
		
		super(dApp, self).__init__(properties, *args, **kwargs)
		# egl: added the option of keeping the main form hidden
		# initially. The default behavior is for it to be shown, as usual.
		self.showMainFormOnStart = True
		self._wasSetup = False
		self._cryptoProvider = None
		# Track names of menus whose MRUs need to be persisted. Set
		# the key for each entry to the menu caption, and the value to
		# the bound function.
		self._persistentMRUs = {}

		# For simple UI apps, this allows the app object to be created
		# and started in one step. It also suppresses the display of
		# the main form.
		if selfStart:
			self.showMainFormOnStart = False
			self.setup()

		self._afterInit()
		self.autoBindEvents()
		

	def setup(self, initUI=True):
		"""Set up the application object."""
		# dabo is going to want to import various things from the Home Directory
		if self.HomeDirectory not in sys.path:
			sys.path.append(self.HomeDirectory)
		if not self.getAppInfo("appName"):
			self.setAppInfo("appName", "Dabo Application")
		if not self.getAppInfo("appShortName"):
			self.setAppInfo("appShortName", self.getAppInfo("appName").replace(" ", ""))
		if not self.getAppInfo("appVersion"):
				self.setAppInfo("appVersion", "")
		if not self.getAppInfo("vendorName"):
			self.setAppInfo("vendorName", "")

		self._initDB()
		
		if initUI:
			self._initUI()
			if self.UI is not None:
				if self.showSplashScreen:
					#self.uiApp = dabo.ui.uiApp(self, callback=self.initUIApp)
					self.uiApp = dabo.ui.getUiApp(self, callback=self.initUIApp)
				else:
					#self.uiApp = dabo.ui.uiApp(self, callback=None)
					self.uiApp = dabo.ui.getUiApp(self, callback=None)
					self.initUIApp()
		else:
			self.uiApp = None
		# Flip the flag
		self._wasSetup = True


	def initUIApp(self):
		"""Callback from the initial app setup. Used to allow the 
		splash screen, if any, to be shown quickly.
		"""
		self.uiApp.setup()
		
	
	def start(self):
		"""Start the application event loop."""
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
			
			self._retrieveMRUs()
			self.uiApp.start(self)
		self.finish()


	def finish(self):
		"""Called when the application event loop has ended."""
		self._persistMRU()
		self.uiApp.finish()
		self.closeConnections()
		dabo.infoLog.write(_("Application finished."))


	def _persistMRU(self):
		"""Persist any MRU lists to disk."""
		base = "MRU.%s" % self.getAppInfo("appName")
		self.deleteAllUserSettings(base)		
		for cap in self._persistentMRUs.keys():
			mruList = self.uiApp.getMRUListForMenu(cap)
			setName = ".".join((base, cap))
			self.setUserSetting(setName, mruList)
	
	
	def _retrieveMRUs(self):
		"""Retrieve any saved MRU lists."""
		base = "MRU.%s" % self.getAppInfo("appName")
		for cap, fcn in self._persistentMRUs.items():
			itms = self.getUserSetting(".".join((base, cap)))
			if itms:
				# Should be a list of items. Add 'em in reverse order
				for itm in itms:
					self.uiApp.addToMRU(cap, itm, fcn)
		

	def getAppInfo(self, item):
		"""Look up the item, and return the value."""
		try:
			retVal = self._appInfo[item]
		except KeyError:
			retVal = None
		return retVal


	def setAppInfo(self, item, value):
		"""Set item to value in the appinfo table."""
		self._appInfo[item] = value


	def getUserSettingKeys(self, spec):
		"""Return a list of all keys underneath <spec> in the user settings table.
		
		For example, if spec is "appWizard.dbDefaults", and there are
		userSettings entries for:
			appWizard.dbDefaults.pkm.Host
			appWizard.dbDefaults.pkm.User
			appWizard.dbDefaults.egl.Host
			
		The return value would be ["pkm", "egl"]
		"""
		if self.UserSettingProvider:
			return self.UserSettingProvider.getUserSettingKeys(spec)
		return None


	def getUserSetting(self, item, default=None, user="*", system="*"):
		"""Return the value of the item in the user settings table."""
		if self.UserSettingProvider:
			return self.UserSettingProvider.getUserSetting(item, default, user, system)
		return None


	def setUserSetting(self, item, value):
		"""Persist a value to the user settings file."""
		if self.UserSettingProvider:
			self.UserSettingProvider.setUserSetting(item, value)
	
	
	def deleteUserSetting(self, item):
		"""Removes the given item from the user settings file."""
		if self.UserSettingProvider:
			self.UserSettingProvider.deleteUserSetting(item)
	
	
	def deleteAllUserSettings(self, spec):
		"""Deletes all settings that begin with the supplied spec."""
		if self.UserSettingProvider:
			self.UserSettingProvider.deleteAllUserSettings(spec)
		
		
	def getUserCaption(self):
		""" Return the full name of the currently logged-on user."""
		if self.SecurityManager:
			return self.SecurityManager.UserCaption
		else:
			return None
			

	# These two methods pass encryption/decryption requests
	# to the Crypto object
	def encrypt(self, val):
		"""Return the encrypted string value. The request is passed 
		to the Crypto object for processing.
		"""
		return self.Crypto.encrypt(val)
		

	def decrypt(self, val):
		"""Return decrypted string value. The request is passed to 
		the Crypto object for processing.
		"""
		return self.Crypto.decrypt(val)

	
	def getCharset(self):
		"""Returns one of 'unicode' or 'ascii'."""
		return self.uiApp.charset
		
		
	def _initProperties(self):
		""" Initialize the public properties of the app object."""
		self.uiType   = None    # ("wx", "qt", "curses", "http", etc.)
		#self.uiModule = None

		# Initialize UI collections
		self.uiForms = Collection()
		self.uiMenus = Collection()
		self.uiToolBars = Collection()
		self.uiResources = {}

		# Initialize DB collections
		self.dbConnectionDefs = {} 
		self.dbConnections = {}

		self._appInfo = {}
		super(dApp, self)._initProperties()

		
	def _initDB(self):
		"""Set the available connection definitions for use by the app. 

		First read in all .cnxml files. If no such XML definition files exist,
		check for a python code definition file named 'dbConnectionDefs.py'.
		"""
		connDefs = {}

		# Import any .cnxml files in HomeDir and/or HomeDir/db:
		for dbDir in (os.path.join(self.HomeDirectory, "db"), self.HomeDirectory):
			if os.path.exists(dbDir) and os.path.isdir(dbDir):
				files = glob.glob(os.path.join(dbDir, "*.cnxml"))
				for f in files:
					connDefs.update(importConnections(f))
		
		# Import any python code connection definitions (the "old" way).
		try:
			import dbConnectionDefs
			connDefs.update(dbConnectionDefs.getDefs())
		except:
			pass
		
		# For each connection definition, add an entry to 
		# self.dbConnectionDefs that contains a key on the 
		# name, and a value of a dConnectInfo object.
		for k,v in connDefs.items():
			ci = dabo.db.dConnectInfo()
			ci.setConnInfo(v)
			self.dbConnectionDefs[k] = ci

		dabo.infoLog.write(_("%s database connection definition(s) loaded.") 
			% (len(self.dbConnectionDefs)))


	def _initUI(self):
		""" Set the user-interface library for the application. Ignored 
		if the UI was already explicitly set by user code.
		"""
		if self.UI is None and not self._uiAlreadySet:
			# For now, default to wx, but it should be enhanced to read an
			# application config file. Actually, that may not be necessary, as the
			# user's main.py can just set the UI directly now: dApp.UI = "qt".
			self.UI = "wx"
		else:
			# Custom app code or the dabo.ui module already set this: don't touch
			dabo.infoLog.write(_("User interface already set to '%s', so dApp didn't touch it.") 
					% self.UI)


	def getConnectionByName(self, connName):
		"""Given the name of a connection, returns the actual
		connection. Stores the connection so that multiple requests
		for the same named connection will not open multiple
		connections. If the name doesn't exist in self.dbConnectionDefs,
		then None is returned.
		"""
		if not self.dbConnections.has_key(connName):
			if self.dbConnectionDefs.has_key(connName):
				ci = self.dbConnectionDefs[connName]
				self.dbConnections[connName] = dabo.db.dConnection(ci)
		try:
			ret = self.dbConnections[connName]
		except KeyError:
			ret = None
		return ret
	
	
	def getConnectionNames(self):
		"""Returns a list of all defined connection names"""
		return self.dbConnectionDefs.keys()
		
		
	def closeConnections(self):
		"""Cleanup as the app is exiting."""
		for conn in self.dbConnections:
			try:
				conn.close()
			except:
				pass
	
	
	def addConnectInfo(self, ci, name=None):
		if name is None:
			try:
				name = ci.Name
			except:
				# Use a default name
				name = "%s@%s" % (ci.User, ci.Host)
		self.dbConnectionDefs[name] = ci
	

	def addConnectFile(self, connFile):
		"""Accepts a cnxml file path, and reads in the connections
		defined in it, adding them to self.dbConnectionDefs.
		"""
		if os.path.exists(connFile):
			connDefs = importConnections(connFile)
			# For each connection definition, add an entry to 
			# self.dbConnectionDefs that contains a key on the 
			# name, and a value of a dConnectInfo object.
			for k,v in connDefs.items():
				ci = dabo.db.dConnectInfo()
				ci.setConnInfo(v)
				self.dbConnectionDefs[k] = ci
	

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
	def onEditFindAlone(self, evt):
		self.uiApp.onEditFindAlone(evt)
	def onEditFindAgain(self, evt):
		self.uiApp.onEditFindAgain(evt)
	def onShowSizerLines(self, evt):
		self.uiApp.onShowSizerLines(evt)
	def onEditPreferences(self, evt):
		try:
			self.ActiveForm.onEditPreferences(evt)
		except:
			self.uiApp.onEditPreferences(evt)
	# These handle MRU menu requests
	def addToMRU(self, menu, prmpt, bindfunc=None):
		self.uiApp.addToMRU(menu, prmpt, bindfunc)
	def onMenuOpenMRU(self, menu):
		self.uiApp.onMenuOpenMRU(menu)
	############################	
	
	
	def copyToClipboard(self, txt):
		"""Place the passed text onto the clipboard."""
		self.uiApp.copyToClipboard(txt)
		

	def onHelpAbout(self, evt):
		import dabo.ui.dialogs.about as about
		dlg = about.About(self.MainForm)
		dlg.show()


	def _getActiveForm(self):
		if hasattr(self, "uiApp") and self.uiApp is not None:
			return self.uiApp.ActiveForm
		else:
			return None
			
	def _setActiveForm(self, frm):
		if hasattr(self, "uiApp") and self.uiApp is not None:
			self.uiApp._setActiveForm(frm)
		else:
			dabo.errorLog.write(_("Can't set ActiveForm: no uiApp."))
	

	def _getCrypto(self):
		if self._cryptoProvider is None:
			# Use the default crypto
			self._cryptoProvider = SimpleCrypt()
		return self._cryptoProvider

	def _setCrypto(self, val):
		self._cryptoProvider = val


	def _getDrawSizerOutlines(self):
		return self.uiApp.DrawSizerOutlines
	
	def _setDrawSizerOutlines(self, val):
		self.uiApp.DrawSizerOutlines = val
	

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
			if hd is None or len(hd.strip()) == 0:
				# punt:
				hd = os.getcwd()

			if os.path.split(hd)[1][-4:].lower() in (".zip", ".exe"):
				# mangle HomeDirectory to not be the py2exe library.zip file,
				# but the containing directory (the directory where the exe lives)
				hd = os.path.split(hd)[0]
			self._homeDirectory = hd			
		return hd
		
	def _setHomeDirectory(self, val):
		if os.path.exists(val):
			self._homeDirectory = os.path.abspath(val)
		else:
			raise ValueError, _("%s: Path does not exist.") % val

				
	def _getMainForm(self):
		try:
			frm = self._mainForm
		except AttributeError:
			frm = None
			self._mainForm = None
		return frm
			
	def _setMainForm(self, val):
		self.uiApp.setMainForm(val)
		self._mainForm = val

				
	def _getMainFormClass(self):
		try:
			cls = self._mainFormClass
		except AttributeError:
			cls = dabo.ui.dFormMain
			self._mainFormClass = cls
		return cls
			
	def _setMainFormClass(self, val):
		self._mainFormClass = val
		
		
	def _getNoneDisp(self):
		v = self._noneDisplay = getattr(self, "_noneDisplay", _("< None >"))
		return v

	def _setNoneDisp(self, val):
		assert isinstance(val, basestring)
		self._noneDisplay = val
		

	def _getPlatform(self):
		try:
			uiApp = self.uiApp
		except AttributeError:
			uiApp = None
		if uiApp is not None:
			return self.uiApp._getPlatform()
		else:
			return "?"


	def _getSearchDelay(self):
		try:
			return self._searchDelay
		except AttributeError:
			## I've found that a value of 300 isn't too fast nor too slow:
			return 300
			
	def _setSearchDelay(self, value):
		self._searchDelay = int(value)			

			
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
			
			
	def _getShowCommandWindowMenu(self):
		try:
			v = self._showCommandWindowMenu
		except AttributeError:
			v = self._showCommandWindowMenu = True
		return v
			
	def _setShowCommandWindowMenu(self, val):
		self._showCommandWindowMenu = bool(val)
			
			
	def _getUI(self):
		try:
			return dabo.ui.getUIType()
		except AttributeError:
			return None
			
	def _setUI(self, uiType):
		# Load the appropriate ui module. dabo.ui will now contain
		# the classes of that library, wx for instance.
		if self.UI is None:
			if uiType is None:
				self._uiAlreadySet = True
				dabo.infoLog.write(_("User interface set set to None."))
			elif dabo.ui.loadUI(uiType):
				self._uiAlreadySet = True
				dabo.infoLog.write(_("User interface set to '%s' by dApp.") % uiType)
			else:
				dabo.infoLog.write(_("Tried to set UI to '%s', but it failed.") % uiType)
		else:
			raise RuntimeError, _("The UI cannot be reset once assigned.")

	
	def _getUserSettingProvider(self):
		try:
			ret = self._userSettingProvider
		except AttributeError:
			if self.UserSettingProviderClass is not None:
				ret = self._userSettingProvider = self.UserSettingProviderClass()
			else:
				ret = self._userSettingProvider = None
		return ret
		
	def _setUserSettingProvider(self, val):
		self._userSettingProvider = val


	def _getUserSettingProviderClass(self):
		try:
			ret = self._userSettingProviderClass
		except AttributeError:
			ret = self._userSettingProviderClass = dUserSettingProvider.dUserSettingProvider
		return ret

	def _setUserSettingProviderClass(self, val):
		self._userSettingProviderClass = val


	ActiveForm = property(_getActiveForm, None, None, 
			_("Returns the form that currently has focus, or None.  (dForm)" ) )
	
	Crypto = property(_getCrypto, _setCrypto, None, 
			_("Reference to the object that provides cryptographic services.  (varies)" ) )
	
	DrawSizerOutlines = property(_getDrawSizerOutlines, _setDrawSizerOutlines, None,
			_("Determines if sizer outlines are drawn on the ActiveForm.  (bool)"))
	
	HomeDirectory = property(_getHomeDirectory, _setHomeDirectory, None,
			_("""Specifies the application's home directory. (string)

			The HomeDirectory is the top-level directory for your application files,
			the directory where your main script lives. You never know what the 
			current directory will be on a given system, but HomeDirectory will always
			get you to your files."""))
		
	MainForm = property(_getMainForm, _setMainForm, None,
			_("""The object reference to the main form of the application, or None.

			The MainForm gets instantiated automatically during application setup, 
			based on the value of MainFormClass. If you want to swap in your own
			MainForm instance, do it after setup() but before start(), as in:

			>>> import dabo
			>>> app = dabo.dApp()
			>>> app.setup()
			>>> app.MainForm = myMainFormInstance
			>>> app.start()"""))
		
	MainFormClass = property(_getMainFormClass, _setMainFormClass, None,
			_("""Specifies the class to instantiate for the main form. Can be a
			class reference, or the path to a .cdxml file.

			Defaults to the dFormMain base class. Set to None if you don't want a 
			main form, or set to your own main form class. Do this before calling
			dApp.start(), as in:

			>>> import dabo
			>>> app = dabo.dApp()
			>>> app.MainFormClass = MyMainFormClass
			>>> app.start()
			(dForm) """))
	
	NoneDisplay = property(_getNoneDisp, _setNoneDisp, None, 
			_("Text to display for null (None) values.  (str)") )
	
	Platform = property(_getPlatform, None, None,
			_("""Returns the platform we are running on. This will be 
			one of 'Mac', 'Win' or 'GTK'.  (str)""") )

	SearchDelay = property(_getSearchDelay, _setSearchDelay, None,
			_("""Specifies the delay before incrementeal searching begins.  (int)

				As the user types, the search string is modified. If the time between
				keystrokes exceeds SearchDelay (milliseconds), the search will run and 
				the search string	will be cleared.

				The value set here in the Application object will become the default for
				all objects that provide incremental searching application-wide.""") )
			
	SecurityManager = property(_getSecurityManager, _setSecurityManager, None, 
			_("""Specifies the Security Manager, if any. 

			You must subclass dSecurityManager, overriding the appropriate hooks 
			and properties, and then set dApp.SecurityManager to an instance of your 
			subclass. There is no security manager by default - you explicitly set 
			this to use Dabo security.""") )

	ShowCommandWindowMenu = property(_getShowCommandWindowMenu,
			_setShowCommandWindowMenu, None, 
			_("""Specifies whether the command window option is shown in the menu.

			If True (the default), there will be a File|Command Window option
			available in the base menu. If False, your code can still start the 
			command window by calling app.showCommandWindow() directly.""") )

	UI = property(_getUI, _setUI, None, 
			_("""Specifies the user interface to load, or None. (str)

			This is the user interface library, such as 'wx' or 'tk'. Note that
			'wx' is the only supported user interface library at this point."""))

	UserSettingProvider = property(_getUserSettingProvider, 
			_setUserSettingProvider, None,
			_("""Specifies the reference to the object providing user preference persistence.
			
			The default UserSettingProvider will save user preferences inside the .dabo
			directory inside the user's home directory."""))

	UserSettingProviderClass = property(_getUserSettingProviderClass,
			_setUserSettingProviderClass, None,
			_("""Specifies the class to use for user preference persistence.
			
			The default UserSettingProviderClass will save user preferences inside the .dabo
			directory inside the user's home directory, and will be instantiated by Dabo
			automatically."""))

