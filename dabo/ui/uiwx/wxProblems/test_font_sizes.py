# -*- coding: utf-8 -*-
import sys
import wx

fontSizes = [int(a) for a in sys.argv[1:]]

if not fontSizes:
	fontSizes = [8, 10, 12, 14]

app = wx.App()
frm = wx.Frame(None)
pan = wx.Panel(frm)

offset = (0,0)
for fontSize in fontSizes:
	but = wx.Button(pan, -1, "%s pt" % fontSize)
	but.SetPosition(offset)
	font = but.GetFont()
	font.SetPointSize(fontSize)
	but.SetFont(font)
	offset = (offset[0]+10, offset[1]+30)

	# Print out the font's size and extent:
	dc = wx.ClientDC(frm)
	print fontSize, dc.GetFullTextExtent(but.GetLabel(), font)
	del dc

frm.Show()
app.MainLoop()
