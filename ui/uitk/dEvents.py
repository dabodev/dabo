import time, Tkinter
import dabo.ui.dEventsBase as dEventsBase
import dabo.common

eventTypes = {
	"<FocusIn>": "GotFocus",
	"<FocusOut>": "LostFocus"}
	
# from dEventsBase.py, bind the dEvent names to Tkinter event sequences:
#Activate = "<Activate>"
#Close
#Create
#Deactivate = "<Deactivate>"
#Destroy
#Hit
#ItemPicked
GotFocus = "<FocusIn>"
#KeyChar
#KeyDown
#KeyUp
LostFocus = "<FocusOut>"
#MouseEnter
#MouseLeave
#MouseLeftClick
#MouseLeftDoubleClick
#MouseRightClick
#MouseLeftDown
#MouseLeftUp
#MouseRightDown
#MouseRightUp
#PageEnter
#PageLeave
#RowNumChanged
#ValueRefresh
	
# Base class for dabo events:
class dEvent(object, Tkinter.Event):
		
	def __init__(self, eventType, eventObject, _nativeEvent=None):
		self._eventType = eventType
		self._eventObject = eventObject
		self._nativeEvent = _nativeEvent

		self._insertEventData()
		self._logEvent()
		
				
	def stop(self):
		""" Stop the event from being handled by any more event handlers.
		"""
		pass
		
		
	def stopPropagation(self):
		""" Stop the event from propagating up in the containership hierarchy.
		"""
		pass

		
	def _insertEventData(self):
		""" Place wx-specific stuff into the ui-agnostic EventData dictionary.
		"""
		self._extraLogInfo = ""
		self.EventData = {}		
		tkEvt = self._nativeEvent
		
		if tkEvt is not None:
			self.EventData["timestamp"] = time.localtime()

# 							
# 			if isinstance(wxEvt, wx.KeyEvent) or isinstance(wxEvt, wx.MouseEvent):
# 				self.EventData["mousePosition"] = wxEvt.GetPositionTuple()
# 				self.EventData["altDown"] = wxEvt.AltDown()
# 				self.EventData["commandDown"] = wxEvt.CmdDown()
# 				self.EventData["controlDown"] = wxEvt.ControlDown()
# 				self.EventData["metaDown"] = wxEvt.MetaDown()
# 				self.EventData["shiftDown"] = wxEvt.ShiftDown()
# 				
# 			if isinstance(wxEvt, wx.KeyEvent):
# 				self.EventData["keyCode"] = wxEvt.GetKeyCode()
# 				self.EventData["rawKeyCode"] = wxEvt.GetRawKeyCode()
# 				self.EventData["rawKeyFlags"] = wxEvt.GetRawKeyFlags()
# 				self.EventData["unicodeChar"] = wxEvt.GetUniChar()
# 				self.EventData["unicodeKey"] = wxEvt.GetUnicodeKey()
# 				self.EventData["hasModifiers"] = wxEvt.HasModifiers()
# 				
# 				self._extraLogInfo = "KeyCode: %s RawKeyCode: %s" % (self.EventData["keyCode"], 
# 					self.EventData["rawKeyCode"])
# 
# 			elif isinstance(wxEvt, wx.MouseEvent):
# 				self._extraLogInfo = "X:%s Y:%s" % (self.EventData["mousePosition"][0], 
# 					self.EventData["mousePosition"][1])
				
			
	def _logEvent(self):
		""" Log the event if the event object's LogEvents property is set.
		"""
		try:
			logEvents = self._eventObject.LogEvents
		except AttributeError:
			logEvents = []
		for eventName in logEvents:
			if eventName.lower() == "all" or eventName == self._eventType:
				dabo.infoLog.write("dEvent Fired: %s.%s %s" % (self._eventObject.getAbsoluteName(), 
					eventTypes[self._eventType],
					self._extraLogInfo))
				break

	def __getattr__(self, att):
		return getattr(self._nativeEvent, att)

	def _getEventObject(self):
		return self._eventObject
		
	def _setEventObject(self, obj):
		self._eventObject = obj
	
	def _getEventData(self):
		return self._eventData
		
	def _setEventData(self, dict):
		self._eventData = dict
	
	EventObject = property(_getEventObject, _setEventObject, None, 
		"References the object that emitted the event.")
		
	EventData = property(_getEventData, _setEventData, None,
		"Dictionary of data name/value pairs associated with the event.")
		

