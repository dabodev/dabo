import wx, dabo
from dLabel import dLabel
from dTextBox import dTextBox
from dDialog import dDialog
from dCommandButton import dCommandButton
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
		dLogin.doDefault()
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
		
		self.addObject(dCommandButton, 'cmdAccept')
		self.addObject(dCommandButton, 'cmdCancel')
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
		dLogin.doDefault()
		mainSizer = self.GetSizer()		
		
		mainSizer.Add((0,5))
		
		bs1 = wx.BoxSizer(wx.HORIZONTAL)
		bs1.Add(self.bm)

		bs1.Add((23,0))
		
		vs = wx.BoxSizer(wx.VERTICAL)			
		bs = wx.BoxSizer(wx.HORIZONTAL)
		
		bs.Add(self.lblUserName)
		bs.Add(self.txtUserName, 1)
		bs.Add((5,0))
		vs.Add(bs, 1, wx.EXPAND)
		
		bs = wx.BoxSizer(wx.HORIZONTAL)
		bs.Add(self.lblPassword)
		bs.Add(self.txtPassword, 1)
		bs.Add((5,0))
		vs.Add(bs, 1, wx.EXPAND)
		
		bs1.Add(vs, 1)
		mainSizer.Add(bs1, 1, wx.EXPAND)
		
		mainSizer.Add((0,15))
		
		mainSizer.Add(self.lblMessage, 1, wx.EXPAND)
		
		bs = wx.BoxSizer(wx.HORIZONTAL)
		bs.Add(self.cmdAccept, 0, wx.ALIGN_BOTTOM)
		bs.Add((3,0))	
		bs.Add(self.cmdCancel, 0, wx.ALIGN_BOTTOM)
		bs.Add((5,0))
		mainSizer.Add(bs, 1, wx.ALIGN_RIGHT)
		mainSizer.Add((0,5))
		mainSizer.Layout()

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
		self.GetSizer().Layout()
				
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
