import wx, wx.py
import dabo, dabo.ui

dabo.ui.loadUI("wx")

class dShell(dabo.ui.dForm):
	def initProperties(self):
		print "props", self
		self.fillMenu()
		#dShell.doDefault()
		super(dShell, self).initProperties()
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


	def fillMenu(self):
		viewMenu = self.MenuBar.getMenu("View")
		if viewMenu.Children:
			viewMenu.appendSeparator()
		viewMenu.append("Zoom &In\tCtrl+=", bindfunc=self.onViewZoomIn, 
				bmp="zoomIn", help="Zoom In")
		viewMenu.append("&Normal Zoom\tCtrl+/", bindfunc=self.onViewZoomNormal, 
				bmp="zoomNormal", help="Normal Zoom")
		viewMenu.append("Zoom &Out\tCtrl+-", bindfunc=self.onViewZoomOut, 
				bmp="zoomOut", help="Zoom Out")


	def onViewZoomIn(self, evt):
		self.shell.SetZoom(self.shell.GetZoom()+1)

	def onViewZoomNormal(self, evt):
		self.shell.SetZoom(0)

	def onViewZoomOut(self, evt):
		self.shell.SetZoom(self.shell.GetZoom()-1)
	


if __name__ == "__main__":
	app = dabo.dApp()
	app.MainFormClass = dShell
	app.setup()
	app.start()
