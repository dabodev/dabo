import sys
import wx
import dabo
import dForm

class dAbout(dForm.dForm):
	def initStyleProperties(self):
		self.BorderStyle = None
		dAbout.doDefault()
		
	def initProperties(self):
		dAbout.doDefault()
		self.BackColor = "White"
		self.MenuBar = None
		self.ShowStatusBar = False
		
	def initEvents(self):
		# Destroy the window when clicked or deactivated:
		self.bindEvent(dabo.dEvents.MouseLeftDown, self.onClear)
		self.bindEvent(dabo.dEvents.MouseRightDown, self.onClear)
		self.bindEvent(dabo.dEvents.Deactivate, self.onClear)

		self.bindEvent(dabo.dEvents.Paint, self.__onPaint)
		
	def afterInit(self):
		dAbout.doDefault()
		self.CenterOnScreen()
		self.SetFocus()


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
		py_version = sys.version.split()[0]
		if app:
			dabo_version = app.getAppInfo("appVersion")
			dabo_appName = app.getAppInfo("appName")
		else:
			dabo_version = "?"
			dabo_appName = "Dabo"
		lbl = "%s %s" % (dabo_appName, dabo_version)
		return lbl
		
def main():
	app = dabo.dApp()
	app.MainFormClass = dAbout
	app.setup()
	app.start()

if __name__ == '__main__':
	main()


