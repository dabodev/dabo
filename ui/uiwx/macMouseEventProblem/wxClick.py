import wx

class TestFrame(wx.Frame):
	def __init__(self, parent, id):
		super(TestFrame, self).__init__(parent=parent, id=id)
		self.SetTitle("WX")
		self.SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.SetSize((300, 400))
		self.Bind(wx.EVT_LEFT_DOWN, self.onMDown)
		self.Bind(wx.EVT_LEFT_UP, self.onMUp)
	
	
	def onMDown(self, evt):
		print "LEFT DOWN"
	
	def onMUp(self, evt):
		print "LEFT UP"
	


if __name__ == '__main__':
	app = wx.PySimpleApp()
	frm = TestFrame(None, -1)
	but = wx.Button(frm, -1, "t")
	frm.Show(1)
	app.MainLoop()
