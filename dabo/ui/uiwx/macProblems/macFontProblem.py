import wx

class TestFrame(wx.Frame):
	def __init__(self, parent, id):
		super(TestFrame, self).__init__(parent=parent, id=id)
		self.SetTitle("wx Font BoldItalic test")
		self.SetSize((300, 400))

		self.tx1 = wx.TextCtrl(self, -1)
		self.tx1.SetValue("Click button")
		self.tx1.SetPosition( (20,20) )
		self.tx1.Name = "Text1"

		but = wx.Button(self, -1, "test")
		but.Bind(wx.EVT_BUTTON, self.onBut)

	def onBut(self, evt):
		self.setFont()
		self.printFont()

	def setFont(self):
		print "----button click----"
		font = self.tx1.GetFont()
		if font.GetWeight() == wx.FONTWEIGHT_NORMAL:
			print "font is not bold; set to bold"
			font.SetWeight(wx.FONTWEIGHT_BOLD)
			self.tx1.SetFont(font)
			return

		print "font was already bold"

		if font.GetStyle() == wx.FONTSTYLE_NORMAL:
			print "font is not italic; set to italic"
			font.SetStyle(wx.FONTSTYLE_ITALIC)
			self.tx1.SetFont(font)
			return

		print "font was already italic"

	def printFont(self):
		font = self.tx1.GetFont()
		print "Font says it is %s and %s." % (font.GetWeightString(), font.GetStyleString())

		
		

if __name__ == '__main__':
	app = wx.PySimpleApp()
	frm = TestFrame(None, -1)
	frm.Show(1)
	app.MainLoop()

