# -*- coding: utf-8 -*-
import time
import dabo
from dabo.dObject import dObject
from dLocalize import _


class dSecurityManager(dObject):
	"""Class providing security services for Dabo applications, such as the
	user logging in.
	"""
	def login(self):
		"""Ask the ui to display the login form to the user.

		Validate the results, and return True if validation succeeds.
		"""

		ret = False
		message = self.LoginMessage
		for attempt in range(self.LoginAttemptsAllowed):
			if attempt > 0:
				num, allwd = attempt+1, self.LoginAttemptsAllowed
				message = _("Login incorrect, please try again. (%(num)s/%(allwd)s)") % locals()
			loginInfo = self.Application.getLoginInfo(message)

			if isinstance(loginInfo[1], dict):
				# loginInfo variable is a tuple (userName (str), loginInfo (dict)).
				# Dictionary keys are: user, password, connection.
				user = loginInfo[1]["user"]
				password = loginInfo[1]
			else:
				# loginInfo variable is a tuple of user name and password.
				user = loginInfo[0]
				password = loginInfo[1]

			if user is None:
				# login form canceled.
				break

			if self.validateLogin(user, password):
				self.__userName = user
				self.UserCaption = self.getUserCaptionFromUserName(user)
				self.__userGroups = self.getUserGroupsFromUserName(user)
				ret = True
				break
			else:
				self.__userName = None
				self.UserCaption = ''
				self.__userGroups = ()
			time.sleep(self.LoginPause)

		if ret:
			self.Application._loggedIn = True
			self.afterLoginSuccess()
		else:
			self.afterLoginFailure()
		return ret


	def afterLoginFailure(self):
		""" Subclass hook called after an unsuccessful login attempt."""
		pass


	def afterLoginSuccess(self):
		""" Subclass hook called after a successful login."""
		pass


	def getUserCaptionFromUserName(self, userName):
		""" Return a descriptive name of the user from the short userName.

		This is a subclass hook: you should override this method with your own
		code that converts the short userName into something more descriptive,
		such as 'pmcnett' -> 'Paul McNett'. The default behavior just echoes
		back the userName.
		"""
		return userName


	def getUserGroupsFromUserName(self, userName):
		""" Return the tuple of groups that userName belongs to.

		This is a subclass hook: you must override this method with your own
		code that returns a tuple filled with the groups the user belongs to.
		The identifiers used for the groups must match the group identifiers
		as coded in your business objects.
		"""
		return ()


	def validateLogin(self, user, password):
		""" Return True if the passed user and password combination is valid.

		This is a subclass hook: you must override this method with your own
		code that does whatever is required to verify the login info. This would
		probably include looking up the information in a database.
		"""
		return False


	def _getLoginAttemptsAllowed(self):
		try:
			return self._loginAttemptsAllowed
		except AttributeError:
			return 3

	def _setLoginAttemptsAllowed(self, value):
		self._loginAttemptsAllowed = int(value)


	def _getLoginMessage(self):
		try:
			m = self._loginMessage
		except AttributeError:
			m = self._loginMessage =  _("Please enter your login information.")
		return m

	def _setLoginMessage(self, val):
		self._loginMessage = val


	def _getLoginPause(self):
		try:
			return self._loginPause
		except AttributeError:
			return 0.25

	def _setLoginPause(self, value):
		self._loginPause = float(value)


	def _getRequireAppLogin(self):
		try:
			return self._requireAppLogin
		except AttributeError:
			return True

	def _setRequireAppLogin(self, value):
		self._requireAppLogin = bool(value)


	def _getUserName(self):
		try:
			return self.__userName
		except AttributeError:
			return None


	def _getUserCaption(self):
		try:
			return self._userCaption
		except AttributeError:
			return ''

	def _setUserCaption(self, value):
		if isinstance(value, basestring):
			self._userCaption = value
		else:
			raise TypeError('User caption must be string or unicode.')


	def _getUserGroups(self):
		try:
			return self.__userGroups
		except AttributeError:
			return ()

	LoginAttemptsAllowed = property(_getLoginAttemptsAllowed, _setLoginAttemptsAllowed, None,
		_("""Specifies the number of attempts the user has to login successfully."""))

	LoginMessage = property(_getLoginMessage, _setLoginMessage, None,
		_("""Specifies the message to initially display on the login form."""))

	LoginPause = property(_getLoginPause, _setLoginPause, None,
		_("""Number of seconds to wait between successive login attempts."""))

	RequireAppLogin = property(_getRequireAppLogin, _setRequireAppLogin, None,
		_("""Specifies whether the user is required to login at app startup."""))

	UserCaption = property(_getUserCaption, _setUserCaption, None,
		_("""The long descriptive name of the logged-on user."""))

	UserGroups = property(_getUserGroups, None, None,
		_("""The tuple of groups that the user belongs to.

		Business objects can be configured to selectively allow/deny various types
		of access based on the group(s) of the logged-in user."""))

	UserName = property(_getUserName, None, None,
		_("""The name of the logged-on user. Read-only."""))


if __name__ == "__main__":
	from dabo.dApp import dApp
	app = dApp(MainFormClass=None)
	app.setup()

	class TestSM(dSecurityManager):
		def validateLogin(self, user, passwd):
			print user, passwd
			if user == "paul" and passwd == "23":
				return True
			return False

	app.SecurityManager = TestSM()
	if app.SecurityManager.login():
		app.MainForm = dabo.ui.dFormMain()
		app.start()

