import wx
import dabo
import dabo.ui
import dabo.icons


if dabo.ui.getUIType() is None:
	dabo.ui.loadUI("wx")

from dabo.dLocalize import _
import dabo.dEvents as dEvents
dKeys = dabo.ui.dKeys

class lbl(dabo.ui.dLabel):
	def initProperties(self):	
		self.Alignment = "Right"
		self.AutoResize = False
		self.Width = 100
				
class lblMessage(dabo.ui.dLabel):
	def initProperties(self):
		self.Alignment = "Center"
		self.AutoResize = False
		self.Caption = _("Please enter your login information.")
		self.FontBold = True
		self.FontItalic = True
		self.ForeColor = "Blue"
		self.FontSize = 10

				
class txt(dabo.ui.dTextBox):
	pass
			
class txtPass(txt):
	def initProperties(self):
		self.PasswordEntry = True
		
		
class Login(dabo.ui.dOkCancelDialog):
	def initProperties(self):
		self.AutoSize = True
		self.BorderResizable = True
		if self.Application:
			appName = self.Application.getAppInfo("appName")
		else:
			appName = ''
		if len(appName) > 0:
			self.Caption = "Login to %s" % appName
		else:
			self.Caption = "Please Login"
		self.ShowCaption = False
		self.ShowCloseButton = True
		

	def addControls(self):
		super(Login, self).afterInit()
		
		self.addObject(lbl, 'lblUserName')
		self.addObject(txt, 'txtUserName')
		self.lblUserName.Caption = "User:"
		self.txtUserName.Value = ""

		self.addObject(lbl, 'lblPassword')
		self.addObject(txtPass, 'txtPassword')
		self.lblPassword.Caption = "Password:"
		self.txtPassword.Value = ""
		
		self.addObject(lblMessage, 'lblMessage')

		self.user, self.password = None, None
		
		self.bm = dabo.ui.dImage(self, Picture=dabo.icons.getIconFileName("daboIcon048.png"))
		
		mainSizer = self.Sizer
		mainSizer.append((0,5))
		
		bs1 = dabo.ui.dSizer("horizontal")
		bs1.append(self.bm)

		bs1.append((23,0))
		
		vs = dabo.ui.dSizer("vertical")
		bs = dabo.ui.dSizer("horizontal")
		
		bs.append(self.lblUserName)
		bs.append((5,0))
		bs.append(self.txtUserName, proportion=1)
		vs.append(bs, "expand", 1)
		
		bs = dabo.ui.dSizer("horizontal")
		bs.append(self.lblPassword)
		bs.append((5,0))
		bs.append(self.txtPassword, proportion=1)
		vs.append(bs, "expand", 1)
		
		bs1.append(vs, proportion=1)
		mainSizer.append(bs1, "expand", 1)
		
		mainSizer.append((0,15))
		
		mainSizer.append(self.lblMessage, "expand", 1)
		
		mainSizer.layout()

		# Map enter key to accept button (because DefaultButton doesn't work):
		self.bindKey("enter", self.onOK)

		
	def setMessage(self, message):
		self.lblMessage.Caption = message
		self.Sizer.layout()
				
	def onCancel(self, evt):
		self.user, self.password = None, None
		self.super(evt)
		
	def onOK(self, evt):
		self.user, self.password = self.txtUserName.Value, self.txtPassword.Value
		self.super(evt)
		
		
if __name__ == '__main__':
	app = wx.PySimpleApp()
	form = Login(None)
	form.show()
	print form.user, form.password
