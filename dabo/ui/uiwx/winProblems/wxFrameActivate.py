# -*- coding: utf-8 -*-
import wx

print "On Windows, note the double Activate events..."

app = wx.PySimpleApp()

def onActivate(evt):
	if evt.GetActive():
		print "Activate"
	else:
		print "Deactivate"

frame = wx.Frame(None, -1)
frame.Bind(wx.EVT_ACTIVATE, onActivate)

frame.Show()
app.MainLoop()