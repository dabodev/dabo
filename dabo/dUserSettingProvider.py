# -*- coding: utf-8 -*-
import dabo
from dabo.dObject import dObject
from dabo.dLocalize import _


class dUserSettingProvider(dObject):
	"""
	Class that manages saving and restoring user settings, such as form
	size and position.
	"""
	def getUserSettingKeys(self, spec):
		"""
		Return a list of all keys underneath <spec>.

		For example, if spec is "appWizard.dbDefaults", and there are
		userSettings entries for:

			appWizard.dbDefaults.pkm.Host
			appWizard.dbDefaults.pkm.User
			appWizard.dbDefaults.egl.Host

		The return value would be ["pkm", "egl"]
		"""
		return self.PreferenceManager.getPrefKeys(spec.lower())


	def getUserSetting(self, item, default=None):
		"""
		Return the value of the user settings table that
		corresponds to the preference key passed.
		"""
		prf = self.PreferenceManager
		parsedItem = item.lower().split(".")
		while len(parsedItem) > 1:
			prf = prf.__getattr__(parsedItem.pop(0))
		key = parsedItem[0]
		ret = prf.getValue(key)
		if ret is None:
			# No such pref key. Return the default
			ret = default
		return ret


	def setUserSetting(self, item, val):
		"""Persist a value to the user settings file."""
		prf = self.PreferenceManager
		parsedItem = item.lower().split(".")
		while len(parsedItem) > 1:
			prf = prf.__getattr__(parsedItem.pop(0))
		key = parsedItem[0]
		prf.setValue(key, val)


	def setUserSettings(self, dct):
		"""Persist a set of setting name: value pairs."""
		for nm, val in dct.items():
			self.setUserSetting(nm, val)


	def deleteUserSetting(self, item):
		"""Removes the specified item from the settings file."""
		self.PreferenceManager.deletePref(item.lower(), False)


	def deleteAllUserSettings(self, spec):
		"""
		Given a spec, deletes all keys that match that spec.
		See the docs for getUserSettingKeys() for an explanation
		on key matching.
		"""
		self.PreferenceManager.deletePref(spec.lower(), True)

