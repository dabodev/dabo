import wx
import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents


class TestForm(dabo.ui.dForm):
	def afterInit(self):
		self.Caption = "DABO"
		self.Size = (300, 400)
		
		self.bindEvent(dEvents.MouseLeftDown, self.onMDown)
		self.bindEvent(dEvents.MouseLeftUp, self.onMUp)
# 		self.Bind(wx.EVT_LEFT_UP, self.WXstopDrag)
		
	
	def onMDown(self, evt):
		print "LEFT DOWN"
	
	def onMUp(self, evt):
		print "LEFT UP"

		

def main():
	app = dabo.dApp()
	app.MainFormClass = TestForm
	app.setup()
	app.start()

if __name__ == '__main__':
	main()

