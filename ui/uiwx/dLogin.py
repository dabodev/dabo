import wx, dabo
from dLabel import dLabel
from dTextBox import dTextBox
from dDialog import dDialog
from dButton import dButton
from dSizer import dSizer
from dabo.dLocalize import _
import dabo.dEvents as dEvents

class lbl(dLabel):
	def initStyleProperties(self):
		self.Alignment = "Right"
		self.AutoResize = False

	def initProperties(self):	
		self.Width = 100
				
class lblMessage(dLabel):
	def initStyleProperties(self):
		self.Alignment = "Center"
		self.AutoResize = False
		
	def initProperties(self):
		self.FontBold = True
		self.FontItalic = True
		self.ForeColor = wx.BLUE
		self.FontSize = 10
		self.Caption = _("Please enter your login information.")

				
class txt(dTextBox):
	pass
			
class txtPass(txt):
	def initStyleProperties(self):
		self.PasswordEntry = True
		
		
class dLogin(dDialog):
	def initStyleProperties(self):
		self.ShowCloseButton = True
		self.ShowCaption = False
		self.BorderResizable = True
		
	def initProperties(self):
		#dLogin.doDefault()
		super(dLogin, self).initProperties()
		if self.Application:
			appName = self.Application.getAppInfo("appName")
		else:
			appName = ''
		if len(appName) > 0:
			self.Caption = "Login to %s" % appName
		else:
			self.Caption = "Please Login"
		
		self.addObject(lbl, 'lblUserName')
		self.addObject(txt, 'txtUserName')
		self.lblUserName.Caption = "User:"
		self.txtUserName.Value = ""
		
		self.addObject(lbl, 'lblPassword')
		self.addObject(txtPass, 'txtPassword')
		self.lblPassword.Caption = "Password:"
		self.txtPassword.Value = ""
		
		self.addObject(dButton, 'cmdAccept')
		self.addObject(dButton, 'cmdCancel')
		self.cmdAccept.Caption = "Accept"
		self.cmdAccept.Default = True
		self.cmdCancel.Caption = "Cancel"
		self.cmdCancel.Cancel = True

		self.addObject(lblMessage, 'lblMessage')

		self.user, self.password = None, None
		
		bm = wx.Bitmap('')
		bm.CopyFromIcon(self.Icon)
		self.bm = wx.StaticBitmap(self, -1, bm)	
			
		
	def afterInit(self):
		#dLogin.doDefault()
		super(dLogin, self).afterInit()
		mainSizer = self.Sizer
		
		mainSizer.append((0,5))
		
		bs1 = dSizer("horizontal")
		bs1.append(self.bm)

		bs1.append((23,0))
		
		vs = dSizer("vertical")
		bs = dSizer("horizontal")
		
		bs.append(self.lblUserName)
		bs.append(self.txtUserName, proportion=1)
		bs.append((5,0))
		vs.append(bs, "expand", 1)
		
		bs = dSizer("horizontal")
		bs.append(self.lblPassword)
		bs.append(self.txtPassword, proportion=1)
		bs.append((5,0))
		vs.append(bs, "expand", 1)
		
		bs1.append(vs, proportion=1)
		mainSizer.append(bs1, "expand", 1)
		
		mainSizer.append((0,15))
		
		mainSizer.append(self.lblMessage, "expand", 1)
		
		bs = dSizer("horizontal")
		bs.append(self.cmdAccept, alignment=("bottom",))
		bs.append((3,0))	
		bs.append(self.cmdCancel, alignment=("bottom",))
		bs.append((5,0))
		mainSizer.append(bs, proportion=1, alignment=("right",))
		mainSizer.append((0,5))
		mainSizer.layout()

		self.cmdAccept.bindEvent(dEvents.Hit, self.onAccept)
		self.cmdCancel.bindEvent(dEvents.Hit, self.onCancel)
		
		# Map escape key to cancelbutton:
		anId = wx.NewId()
		self.acceleratorTable.append((wx.ACCEL_NORMAL, wx.WXK_ESCAPE, anId))
		self.Bind(wx.EVT_MENU, self.onCancel, id=anId)

		# Map enter key to accept button:
		anId = wx.NewId()
		self.acceleratorTable.append((wx.ACCEL_NORMAL, wx.WXK_RETURN, anId))
		self.Bind(wx.EVT_MENU, self.onAccept, id=anId)

		
	def setMessage(self, message):
		self.lblMessage.Caption = message
		self.Sizer.layout()
				
	def onCancel(self, evt):
		self.user, self.password = None, None
		self.Hide()
		
	def onAccept(self, evt):
		self.user, self.password = self.txtUserName.Value, self.txtPassword.Value
		self.Hide()
		
		
if __name__ == '__main__':
	app = wx.PySimpleApp()
	form = dLogin(None)
	form.ShowModal()
	print form.user, form.password
