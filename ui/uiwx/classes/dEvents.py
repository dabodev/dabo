import wx

# Dabo event identifiers:
EVT_ROWNUMCHANGED = wx.NewEventType()
EVT_VALUEREFRESH = wx.NewEventType()
EVT_VALUECHANGED = wx.NewEventType()

# Base class for dabo events:
class dEvent(wx.PyCommandEvent):
	def __init__(self, evtType, id):
		wx.PyCommandEvent.__init__(self, evtType, id)


