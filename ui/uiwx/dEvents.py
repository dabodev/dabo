import wx
import dabo.ui.dEventsBase as dEventsBase

# Assign Dabo event names to wx event objects in a 1:1 fashion:
mapEvents = (
	("CheckBox", "wx.EVT_CHECKBOX"),
	("Choice", "wx.EVT_CHOICE"),
	("Close", "wx.EVT_CLOSE"),
	("Create", "wx.EVT_WINDOW_CREATE"),
	("Destroy", "wx.EVT_WINDOW_DESTROY"),
	("GotFocus", "wx.EVT_SET_FOCUS"),
	("KeyChar", "wx.EVT_CHAR"),
	("KeyDown", "wx.EVT_KEY_DOWN"),
	("KeyUp", "wx.EVT_KEY_UP"),
	("ListbookPageChanged", "wx.EVT_LISTBOOK_PAGE_CHANGED"),
	("LostFocus", "wx.EVT_KILL_FOCUS"),
	("MouseEnter", "wx.EVT_ENTER_WINDOW"),
	("MouseLeave", "wx.EVT_LEAVE_WINDOW"),
	("MouseLeftDoubleClick", "wx.EVT_LEFT_DCLICK"),
	("MouseLeftDown", "wx.EVT_LEFT_DOWN"),
	("MouseLeftUp", "wx.EVT_LEFT_UP"),
	("MouseRightDown", "wx.EVT_RIGHT_DOWN"),
	("MouseRightUp", "wx.EVT_RIGHT_UP"),
	("PageChanged", "wx.EVT_NOTEBOOK_PAGE_CHANGED"),
	("RadioBox", "wx.EVT_RADIOBOX"),
	("Scroll", "wx.EVT_SCROLL"),
	("Spinner", "wx.EVT_SPINCTRL"),
	("Text", "wx.EVT_TEXT"),
	("Timer", "wx.EVT_TIMER"),
	)
	
for event in dEventsBase.events:
	eventName = event[0]
	done = False
	
	for mapEvent in mapEvents:
		if mapEvent[0] == eventName:
			# Map the Dabo event name to the appropriate wx event object.
			exec "%s = %s" % (eventName, mapEvent[1])
			done = True
			exit
	
	if not done:
		# Event is custom (non-wx), or requires more complicated interaction: 
		# assign it to a new event object. 
		exec "%s = wx.PyEventBinder(wx.NewEventType())" % eventName

		
# Base class for dabo events:
class dEvent(wx.PyCommandEvent):
	def __init__(self, evtType, eventObject):
		wx.PyCommandEvent.__init__(self, evtType, eventObject.GetId())
		self.SetEventObject(eventObject)


