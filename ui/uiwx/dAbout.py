import sys
import wx
import dabo
import dForm

class dAbout(dForm.dForm):
	def initProperties(self):
		dAbout.doDefault()
		self.BackColor = "White"
		self.MenuBar = None
		self.ShowStatusBar = False
		self.Caption = "About"
		
	def initEvents(self):
		# Destroy the window when clicked or deactivated:
		self.bindEvent(dabo.dEvents.MouseLeftDown, self.onClear)
		self.bindEvent(dabo.dEvents.MouseRightDown, self.onClear)
		self.bindEvent(dabo.dEvents.Deactivate, self.onClear)

		self.bindEvent(dabo.dEvents.Paint, self.__onPaint)
		
	def afterInit(self):
		dAbout.doDefault()
		self.CenterOnScreen()
		dc = wx.ClientDC(self)
		self.draw(dc)  # doesn't happen on Mac otherwise

	def restoreSizeAndPosition(self):
		pass
		
	def onClear(self, evt):
		self.Destroy()

	def __onPaint(self, evt):
		dc = wx.PaintDC(self)
		self.draw(dc)

	def draw(self, dc):
		# Dabo icon
		bitmap = dabo.ui.dIcons.getIconBitmap("dabo_lettering_100x40")
		
		# The width of the whitespace between the outer rectangle and where content begins
		border = 7
		
		dcWidth, dcHeight = dc.GetSize()
		bmWidth, bmHeight = bitmap.GetSize()

		# Outer rectangle
		dc.DrawRectangle(0, 0, dcWidth, dcHeight)
		
		# Dabo bitmap
		dc.DrawBitmap(bitmap, dcWidth-bmWidth-border, dcHeight-bmHeight-border)

		# Text area:
		lblText = self.getLabelText()
		dc.DrawLabel(lblText, (border, border, dcWidth-(2*border), dcHeight-(2*border)))

	def getLabelText(self):
		app = self.Application
		pyVersion = "%s on %s" % (sys.version.split()[0], sys.platform)
		if app:
			appVersion = app.getAppInfo("appVersion")
			appName = app.getAppInfo("appName")
		else:
			appVersion = "?"
			appName = "Dabo"
		daboVersion = dabo.version["version"]
		uiName = dabo.ui.uiType["longName"]
		uiVersion = "%s on %s" % (dabo.ui.uiType["version"], dabo.ui.uiType["platform"])
		lbl = """%s %s
		
\tDabo %s
\tPython %s
\t%s %s"""

		lbl = lbl % (appName, appVersion, daboVersion, pyVersion, uiName, uiVersion)
		return lbl
		
def main():
	app = dabo.dApp()
	app.MainFormClass = dAbout
	app.setup()
	app.start()

if __name__ == '__main__':
	main()


