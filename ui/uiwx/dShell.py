import wx, wx.py
import dabo, dabo.ui

dabo.ui.loadUI("wx")

class dShell(dabo.ui.dForm):
	def initProperties(self):
		dShell.doDefault()
 		self.shell = wx.py.shell.Shell(self)
		
		# Make 'self' refer to the calling form, or this form if no calling form.
		if self.Parent is None:
			ns = self
		else:
			ns = self.Parent
 		self.shell.interp.locals['self'] = ns

		self.Caption = "dShell: self is %s" % ns.Name
		self.setStatusText("Use this shell to interact with the runtime environment")
		
 		self.Sizer = dabo.ui.dSizer()
 		self.Sizer.append(self.shell, "expand", 1)
        
		self.shell.SetFocus()
		
if __name__ == "__main__":
	app = dabo.dApp()
	app.MainFormClass = dShell
	app.setup()
	app.start()
