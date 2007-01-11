"""
This test shows some oddities with wx.AcceleratorTable. On GTK,
wxPython 2.6.2.1 I'm seeing:

+ A panel or some other control is necessary in order for the
  frame's accelerator table entries to run

+ Not all keys are working:
	- F2, F4, F6, F8, F10, F12 are skipped
	- F9 prints WXK_F10
	- SHIFT prints WXK_ALT
	- ALT skipped
	- PgDn prints WXK_END
	- End is skipped
	- UpArrow prints WXK_RIGHT
	- LeftArrow, RightArrow skipped (DownArrow correctly prints WXK_DOWN)

	Additional testing in a different app reveals that if F1 isn't in the
	accelerator table, and F2 is, that pressing F2 is skipped but pressing
	F1 will fire the event as if F2 were pressed.
"""
import wx

modifier = wx.ACCEL_NORMAL
#modifier = wx.ACCEL_CTRL

app = wx.PySimpleApp()
frm = wx.Frame(None, -1)

# Why is the following necessary for the frame's accelerator table
# to work?
wx.Panel(frm)

accelTable = {}
idKeyMap = {}

def onAccelKey(evt):
	print idKeyMap[evt.GetId()]

for key in [i for i in dir(wx) if i[:4] == "WXK_"]:
	keyCode = getattr(wx, key)
	anId = wx.NewId()
	accelTable[anId] = (modifier, keyCode, anId)
	idKeyMap[anId] = key
	frm.SetAcceleratorTable(wx.AcceleratorTable(accelTable.values()))
	frm.Bind(wx.EVT_MENU, onAccelKey, id=anId)

frm.Show()
app.MainLoop()
