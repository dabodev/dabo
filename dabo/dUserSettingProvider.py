import os
import ConfigParser
import dabo
import dabo.lib.utils as utils


class dUserSettingProvider(dabo.common.dObject):
	def getUserSettingKeys(self, spec):
		"""Return a list of all keys underneath <spec>.
		
		For example, if spec is "appWizard.dbDefaults", and there are
		userSettings entries for:
			appWizard.dbDefaults.pkm.Host
			appWizard.dbDefaults.pkm.User
			appWizard.dbDefaults.egl.Host
			
		The return value would be ["pkm", "egl"]
		"""
		homeDir = self._getHomeDir()
		fileName = self._getFileName()
		configFileName = os.path.join(homeDir, fileName)

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
		
	def getUserSetting(self, item, default=None, user="*", system="*"):
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
		homeDir = self._getHomeDir()
		fileName = self._getFileName()
		configFileName = os.path.join(homeDir, fileName)

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
			value = default

		return value


	def setUserSetting(self, item, value):
		"""Persist a value to the user settings file.
		"""
		homeDir = self._getHomeDir()
		fileName = self._getFileName()
		configFileName = os.path.join(homeDir, fileName)

		cp = ConfigParser.ConfigParser()
		cp.read(configFileName)

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
			
		if not cp.has_section("UserSettings"):
			cp.add_section("UserSettings")
		cp.set("UserSettings", item, str(value))

		if not cp.has_section("UserSettingsValueTypes"):
			cp.add_section("UserSettingsValueTypes")
		cp.set("UserSettingsValueTypes", item, valueType)

		configFile = open(configFileName, "w")
		cp.write(configFile)
		configFile.close()
		
	def _getHomeDir(self):
		"""Return the home directory where the settings file should live."""
		return utils.getUserDaboDirectory()

	def _getFileName(self):
		"""Return the name of the settings file."""
		appName = self.Application.getAppInfo("appShortName")
		return "userSettings-%s.ini" % appName
