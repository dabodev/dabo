import wx

class TestFrame(wx.Frame):
	def __init__(self, parent, id):
		super(TestFrame, self).__init__(parent=parent, id=id)
		self.SetSize((300, 400))

		mb = wx.MenuBar()
		menu = wx.Menu()

		for hotkey in ("ctrl+LEFT", "ctrl+RIGHT", "ctrl+UP", "ctrl+DOWN"): 
			id_ = wx.NewId()
			menu.Append(id_, "%s\t%s" % (hotkey, hotkey))
			self.Bind(wx.EVT_MENU, self.onHotKey, id=id_)

		mb.Append(menu, "Arrow key hotkey test")
		self.SetMenuBar(mb)

	def onHotKey(self, evt):
		print evt.GetEventObject().GetLabel(evt.GetId()).split("\t")[0]	
		

if __name__ == '__main__':
	app = wx.PySimpleApp()
	frm = TestFrame(None, -1)
	frm.Show(1)
	app.MainLoop()

