import wx

MakeMacFail = True

def onDown(evt):
	print "MouseDown"
	if MakeMacFail:
		print "EVT_LEFT_UP will not be received on Mac, because of the"
		print "evt.Skip() in the EVT_LEFT_DOWN event handler."
		evt.Skip()
	else:
		print "EVT_LEFT_UP will be received on Mac, because"
		print "evt.Skip() was *not* called in the EVT_LEFT_DOWN event handler."

def onUp(evt):
	print "MouseUp"

app = wx.PySimpleApp()
frm = wx.Frame(None, -1, "Left-click on the panel")
pan = wx.Panel(frm)
pan.Bind(wx.EVT_LEFT_DOWN, onDown)
pan.Bind(wx.EVT_LEFT_UP, onUp)
frm.Show(1)
app.MainLoop()
