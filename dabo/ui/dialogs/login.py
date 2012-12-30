# -*- coding: utf-8 -*-
import dabo

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dabo.ui
import dabo.icons
from dabo.dLocalize import _


class Lbl(dabo.ui.dLabel):
	def initProperties(self):
		self.Alignment = "Right"
		self.AutoResize = False
		self.Width = 125

class LblMessage(dabo.ui.dLabel):
	def initProperties(self):
		self.Alignment = "Center"
		self.AutoResize = False
		self.Caption = _("Please enter your login information.")
		self.FontBold = True
		self.FontItalic = True
		self.ForeColor = "Blue"
		self.FontSize = 10


class Txt(dabo.ui.dTextBox):
	def initProperties(self):
		self.Width = 175


class TxtPass(Txt):
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
			self.Caption = _("Login to %s") % appName
		else:
			self.Caption = _("Please Login")
		self.ShowCaption = False
		self.ShowCloseButton = True


	def addControls(self):
		super(Login, self).addControls()

		self.lblUserName = Lbl(self, Caption=_("User:"))
		self.txtUserName = Txt(self, SaveRestoreValue=True, RegID="txtUserName")

		self.lblPassword = Lbl(self, Caption=_("Password:"))
		self.txtPassword = TxtPass(self, Value="")

		self.lblMessage = LblMessage(self)

		self.user, self.password = None, None

		self.bm = dabo.ui.dImage(self, Picture=self.IconFile)

		mainSizer = self.Sizer
		mainSizer.appendSpacer(15)

		bs1 = dabo.ui.dSizer("h")
		bs1.append(self.bm)

		bs1.appendSpacer(23)

		vs = dabo.ui.dSizer("v")
		bs = dabo.ui.dSizer("h")

		bs.append(self.lblUserName, alignment="middle")
		bs.appendSpacer(5)
		bs.append(self.txtUserName, 1)
		vs.append1x(bs)

		vs.appendSpacer(5)

		bs = dabo.ui.dSizer("h")
		bs.append(self.lblPassword, alignment="middle")
		bs.appendSpacer(5)
		bs.append(self.txtPassword, 1)
		vs.append1x(bs)

		bs1.append(vs, 1)
		mainSizer.append1x(bs1)

		mainSizer.appendSpacer(10)
		mainSizer.append1x(self.lblMessage)
		mainSizer.appendSpacer(10)

		mainSizer.layout()

		self.txtUserName.setFocus()


	def setMessage(self, message):
		self.lblMessage.Caption = message
		self.Sizer.layout()

	def runCancel(self):
		self.user, self.password = None, None
		super(Login, self).runCancel()

	def onEnterKey(self, evt):
		self.runOK()

	def runOK(self):
		self.user, self.password = self.txtUserName.Value, self.txtPassword.Value
		super(Login, self).runOK()


	def _getIconFile(self):
		ret = getattr(self, "_iconFile", None)
		if not ret:
			ret = self._iconFile = dabo.icons.getIconFileName("daboIcon048.png")
		return ret

	def _setIconFile(self, val):
		self._iconFile = val
		self.bm.Picture = val

	IconFile = property(_getIconFile, _setIconFile, None, _("Specifies the icon to use."))


if __name__ == '__main__':
	from dabo.dApp import dApp
	app = dApp(MainFormClass=None)
	app.setup()
	form = Login(None)
	form.show()
	print form.user, form.password
