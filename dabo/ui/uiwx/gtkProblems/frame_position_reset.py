# -*- coding: utf-8 -*-
##- On Gtk, wxPython 2.8.1.1, hiding and showing a wx.Frame resets its
##- position back to its original. Run this test, and reposition the frame,
##- and then click inside the frame. It'll jump back to its original position.

import wx

def onClick(evt):
	frm = evt.GetEventObject()
	print 1, frm.GetPosition()
	frm.Show(False)
	print 2, frm.GetPosition()
	frm.Show()
	print 3, frm.GetPosition()

app = wx.App()
frm = wx.Frame(None)
frm.Bind(wx.EVT_LEFT_DOWN, onClick)

frm.Show()
app.MainLoop()
