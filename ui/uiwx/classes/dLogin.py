from dLabel import dLabel
from dTextBox import dTextBox
from dDialog import dDialog
from dCommandButton import dCommandButton
import wx

class lbl(dLabel):
	def initStyleProperties(self):
		self.Alignment = "Right"
		self.AutoResize = False
	
	def initProperties(self):
		self.Width = 100
		
class txt(dTextBox):
	def initProperties(self):
		self.Width = 175
		
class txtPass(txt):
	def initStyleProperties(self):
		self.PasswordEntry = True
		
		
class dLogin(dDialog):
	def initStyleProperties(self):
		dLogin.doDefault()
		
	def initProperties(self):
		dLogin.doDefault()
		self.Caption = "Login"
		
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

		
	def afterInit(self):
		dLogin.doDefault()
		sz = self.GetSizer()		
		sz.AddSpacer((0,15))
		bs = wx.BoxSizer(wx.HORIZONTAL)
		bs.Add(self.lblUserName)
		bs.Add(self.txtUserName)
		sz.Add(bs)
		
		bs = wx.BoxSizer(wx.HORIZONTAL)
		bs.Add(self.lblPassword)
		bs.Add(self.txtPassword)
		sz.Add(bs)
		
		sz.AddSpacer((0,15))
		
		bs = wx.BoxSizer(wx.HORIZONTAL)
		bs.Add(self.cmdAccept)
		bs.AddSpacer((3,0))
		bs.Add(self.cmdCancel)
		bs.AddSpacer((15,0))
		sz.Add(bs, 1, wx.ALIGN_RIGHT)
		sz.Layout()

		# Size the form to accomodate the size of the controls:
		self.Width = self.txtUserName.Width + self.lblUserName.Width + 30
		self.Height = self.txtUserName.Height + self.lblUserName.Height + 75
		
		self.cmdAccept.Bind(wx.EVT_BUTTON, self.OnAccept)
		self.cmdCancel.Bind(wx.EVT_BUTTON, self.OnCancel)
		
		# Map escape key to cancelbutton:
		anId = wx.NewId()
		self.acceleratorTable.append((wx.ACCEL_NORMAL, wx.WXK_ESCAPE, anId))
		self.Bind(wx.EVT_MENU, self.OnCancel, id=anId)

		# Map enter key to accept button:
		anId = wx.NewId()
		self.acceleratorTable.append((wx.ACCEL_NORMAL, wx.WXK_RETURN, anId))
		self.Bind(wx.EVT_MENU, self.OnAccept, id=anId)
		
		
	def OnCancel(self, evt):
		self.user, self.password = None, None
		self.Close()
		
	def OnAccept(self, evt):
		self.user, self.password = self.txtUserName.Value, self.txtPassword.Value
		self.Close()
		
		
if __name__ == '__main__':
	app = wx.PySimpleApp()
	form = dLogin(None)
	form.ShowModal()
	print form.user, form.password
