# -*- coding: utf-8 -*-
import dabo
import dabo.ui
import myForms


class TestSecurityManager(dabo.dSecurityManager.dSecurityManager):
	""" This is a simple subclass of dSecurityManager, to show how it works.
	
	Try changing self.RequireAppLogin to True, and you should get a login
	form at app startup.
	"""
	def initProperties(self):
		self.LoginMessage = "For this demo, user=dabo, pass=dabo"
		self.RequireAppLogin = True
		
	def validateLogin(self, user, password):
		""" Return True to tell the security manager to accept the login.
		
		This is your hook to do whatever validation is required to determine whether
		the user can login or not.
		"""		
		if user == 'dabo' and password == 'dabo':
			return True
		else:
			return False
			
	def getUserCaptionFromUserName(self, user):
		""" Whatever you return here becomes the value of the UserCaption property.
		
		This is your hook to set the UserCaption to something more descriptive and
		friendly, such as converting pmcnett to 'Paul McNett'.
		"""
		if user == 'dabo':
			return 'Dabo Test User'
		else:
			return '???'
			
	def getUserGroupsFromUserName(self, user):
		""" Return a tuple that lists the user's group membership. 
		
		This is your hook to set the groups this user belongs to, using whatever
		means to determine this your application requires. For instance, perhaps 
		there is a group called 'BaseUser' that all logged in users belong to.
		"""
		return ("BaseUser",)

def main():
	app = dabo.dApp()
	app.BasePrefKey = "demo.apprecipes"
	app.setAppInfo("appName", "Dabo Recipe Demo")

	app.SecurityManager = TestSecurityManager()
	app.setup()
	import myFileOpenMenu
	myFileOpenMenu.fill(app.MainForm)
	app.start()
	
	
if __name__ == "__main__":
	main()
