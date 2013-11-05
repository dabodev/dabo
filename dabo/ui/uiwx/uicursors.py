# -*- coding: utf-8 -*-
import wx

Cursor_Arrow = wx.CURSOR_ARROW
Cursor_Right_Arrow = wx.CURSOR_RIGHT_ARROW
Cursor_Blank = wx.CURSOR_BLANK
Cursor_Bullseye = wx.CURSOR_BULLSEYE
Cursor_Char = wx.CURSOR_CHAR
Cursor_Cross = wx.CURSOR_CROSS
Cursor_Hand = wx.CURSOR_HAND
Cursor_Ibeam = wx.CURSOR_IBEAM
Cursor_Left_Button = wx.CURSOR_LEFT_BUTTON
Cursor_Magnifier = wx.CURSOR_MAGNIFIER
Cursor_Middle_Button = wx.CURSOR_MIDDLE_BUTTON
Cursor_No_Entry = wx.CURSOR_NO_ENTRY
Cursor_Paint_Brush = wx.CURSOR_PAINT_BRUSH
Cursor_Pencil = wx.CURSOR_PENCIL
Cursor_Point_Left = wx.CURSOR_POINT_LEFT
Cursor_Point_Right = wx.CURSOR_POINT_RIGHT
Cursor_Question_Arrow = wx.CURSOR_QUESTION_ARROW
Cursor_Right_Button = wx.CURSOR_RIGHT_BUTTON
Cursor_Size_NWSE = wx.CURSOR_SIZENWSE
Cursor_Size_NESW = wx.CURSOR_SIZENESW
Cursor_Size_NS = wx.CURSOR_SIZENS
Cursor_Size_WE = wx.CURSOR_SIZEWE
Cursor_Sizing = wx.CURSOR_SIZING
Cursor_Spraycan = wx.CURSOR_SPRAYCAN
Cursor_Wait = wx.CURSOR_WAIT
Cursor_Watch = wx.CURSOR_WATCH
Cursor_Arrowwait = wx.CURSOR_ARROWWAIT


def getStockCursor(id):
	return wx.StockCursor(id)
