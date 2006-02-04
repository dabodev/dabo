import os
import ConfigParser
import dabo
import dabo.lib.utils as utils
from dabo.dObject import dObject
from dabo.dLocalize import _


class dUserSettingProvider(dObject):
	def afterInit(self):
		"""Set some values to be used throughout the class."""
		self._valSection = "UserSettings"
		self._valTypeSection = "UserSettingsValueTypes"
		
		
	def getParser(self):
		"""Returns a parser with the config file loaded."""
		homeDir = self._getHomeDir()
		fileName = self.SettingsFileName
		configFileName = os.path.join(homeDir, fileName)
		cp = ConfigParser.ConfigParser()
		cp.fileName = configFileName
		cp.read(configFileName)
		if not cp.has_section(self._valSection):
			cp.add_section(self._valSection)
		if not cp.has_section(self._valTypeSection):
			cp.add_section(self._valTypeSection)
		return cp
		

	def getUserSettingKeys(self, spec):
		"""Return a list of all keys underneath <spec>.
		
		For example, if spec is "appWizard.dbDefaults", and there are
		userSettings entries for:
			appWizard.dbDefaults.pkm.Host
			appWizard.dbDefaults.pkm.User
			appWizard.dbDefaults.egl.Host
			
		The return value would be ["pkm", "egl"]
		"""
		cp = self.getParser()
		spec = spec.lower()
		
		try:
			items = cp.items(self._valSection)
		except ConfigParser.NoSectionError:
			items = []
		
		ret = []	
		for item in items:
			wholekey = item[0].lower()
			if wholekey[:len(spec)] == spec:
				nonspec = wholekey[len(spec):]
				while nonspec.startswith("."):
					nonspec = nonspec[1:]
				key = nonspec.split(".")[0]
				if ret.count(key) == 0:
					ret.append(key)
		return ret
		

	def getUserSetting(self, item, default=None, user="*", system="*", cp=None):
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
		if cp is None:
			cp = self.getParser()
		try:
			valueType = cp.get(self._valTypeSection, item)
		except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
			valueType = "C"
		try:
			if valueType == "I":
				value = cp.getint(self._valSection, item)
			elif valueType == "N":
				value = cp.getfloat(self._valSection, item)
			elif valueType == "L":
				value = cp.getboolean(self._valSection, item)
			else:
				value = cp.get(self._valSection, item)
		except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
			value = default
		return value


	def setUserSetting(self, item, value, cp=None):
		"""Persist a value to the user settings file."""
		if cp is None:
			cp = self.getParser()
		if isinstance(value, basestring):
			valueType = "C"
		elif isinstance(value, bool):
			valueType = "L"
		elif isinstance(value, float):
			valueType = "N"
		elif isinstance(value, (int, long)):
			valueType = "I"
		else:
			valueType = "?"
			
		cp.set(self._valSection, item, str(value))
		cp.set(self._valTypeSection, item, valueType)
		configFile = open(cp.fileName, "w")
		cp.write(configFile)
		configFile.close()
		

	def deleteUserSetting(self, item, cp=None):
		"""Removes the specified item from the settings file."""
		if cp is None:
			cp = self.getParser()
		try:
			cp.remove_option(self._valTypeSection, item.lower())
		except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
			pass
		try:
			cp.remove_option(self._valSection, item.lower())
		except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
			pass
		configFile = open(cp.fileName, "w")
		cp.write(configFile)
		configFile.close()


	def deleteAllUserSettings(self, spec, cp=None):
		"""Given a spec, deletes all keys that match that spec.
		See the docs for getUserSettingKeys() for an explanation
		on key matching.
		"""
		if cp is None:
			cp = self.getParser()
		spec = spec.lower()
		try:
			items = cp.items(self._valSection)
		except ConfigParser.NoSectionError:
			items = []
		for item in items:
			key = item[0]
			if key.lower().startswith(spec):
				self.deleteUserSetting(key, cp)


	def _getHomeDir(self):
		"""Return the full path of the directory for the settings file."""
		return utils.getUserDaboDirectory(self.SettingsDirectoryName)


	def _getSettingsDirectoryName(self):
		if hasattr(self, "_settingsDirectoryName"):
			v = self._settingsDirectoryName
		else:
			v = self._settingsDirectoryName = self.Application.getAppInfo("appShortName")
		return v

	def _setSettingsDirectoryName(self, val):
		self._settingsDirectoryName = val


	def _getSettingsFileName(self):
		if hasattr(self, "_settingsFileName"):
			v = self._settingsFileName
		else:
			v = self._settingsFileName = "userSettings-%s.ini" \
					% self.Application.getAppInfo("appShortName")
		return v

	def _setSettingsFileName(self, val):
		self._settingsFileName = val


	SettingsDirectoryName = property(_getSettingsDirectoryName, 
			_setSettingsDirectoryName, None,
			_("""The name of the directory to put the settings file.

				This is just a directory name, not a full path. The path is determined
				by platform conventions."""))

	SettingsFileName = property(_getSettingsFileName, _setSettingsFileName, None,
			_("""The name of the user settings file.

				This is just a file name, not a full path."""))
