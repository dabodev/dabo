import wx

# Dabo event identifiers:
EVT_FIELDCHANGED = wx.NewEventType()
EVT_VALUEREFRESH = wx.NewEventType()

# Base class for dabo events:
class dEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id):
        wx.PyCommandEvent.__init__(self, evtType, id)

       
