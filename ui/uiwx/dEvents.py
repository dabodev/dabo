import time, wx
import dabo.ui.dEventsBase as dEventsBase
import dabo.common

eventTypes = {}

for event in dEventsBase.events:
	eventName = event[0]
	t = wx.NewEventType()
	eventTypes[t] = '%s' % eventName
	exec "%s = wx.PyEventBinder(t,0)" % (eventName,)


# Base class for dabo events:
class dEventBase(object):
		
	def __init__(self, eventType, eventObject, _nativeEvent=None):
		self.SetEventType(eventType)
		self.SetEventObject(eventObject)
		self._nativeEvent = _nativeEvent

		self._insertEventData()
		self._logEvent()
		
		# So user code doesn't need to call Skip():
		self.Skip()

				
	def stop(self):
		""" Stop the event from being handled by any more event handlers.
		"""
		self.Skip(False)
		
		
	def stopPropagation(self):
		""" Stop the event from propagating up in the containership hierarchy.
		"""
		self.StopPropagation()

		
	def _insertEventData(self):
		""" Place wx-specific stuff into the ui-agnostic EventData dictionary.
		"""
		self._extraLogInfo = ""
		self.EventData = {}		
		wxEvt = self._nativeEvent
		
		if wxEvt is not None:
			self.EventData["timestamp"] = time.localtime()

			try:
				self.EventData["selection"] = wxEvt.GetSelection()
			except AttributeError:
				pass
							
			if isinstance(wxEvt, wx.KeyEvent) or isinstance(wxEvt, wx.MouseEvent):
				self.EventData["mousePosition"] = wxEvt.GetPositionTuple()
				self.EventData["altDown"] = wxEvt.AltDown()
				self.EventData["commandDown"] = wxEvt.CmdDown()
				self.EventData["controlDown"] = wxEvt.ControlDown()
				self.EventData["metaDown"] = wxEvt.MetaDown()
				self.EventData["shiftDown"] = wxEvt.ShiftDown()
				
			if isinstance(wxEvt, wx.KeyEvent):
				self.EventData["keyCode"] = wxEvt.GetKeyCode()
				self.EventData["rawKeyCode"] = wxEvt.GetRawKeyCode()
				self.EventData["rawKeyFlags"] = wxEvt.GetRawKeyFlags()
				self.EventData["unicodeChar"] = wxEvt.GetUniChar()
				self.EventData["unicodeKey"] = wxEvt.GetUnicodeKey()
				self.EventData["hasModifiers"] = wxEvt.HasModifiers()
				
				self._extraLogInfo = "KeyCode: %s RawKeyCode: %s" % (self.EventData["keyCode"], 
					self.EventData["rawKeyCode"])

			elif isinstance(wxEvt, wx.MouseEvent):
				self._extraLogInfo = "X:%s Y:%s" % (self.EventData["mousePosition"][0], 
					self.EventData["mousePosition"][1])
				
			
	def _logEvent(self):
		""" Log the event if the event object's LogEvents property is set.
		"""
		try:
			logEvents = self.GetEventObject().LogEvents
		except AttributeError:
			logEvents = []
		for eventName in logEvents:
			if eventName.lower() == "all" or eventName == eventTypes[self.GetEventType()]:
				dabo.infoLog.write("dEvent Fired: %s.%s %s" % (self.GetEventObject().getAbsoluteName(), 
					eventTypes[self.GetEventType()],
					self._extraLogInfo))
				break

	def __getattr__(self, att):
		# I put this in so that user code could have access to the wx event's PEM's,
		# but for some reason really weird values are getting returned. Use the
		# values in the EventData dictionary instead.
		return getattr(self._nativeEvent, att)

	def _getEventObject(self):
		return self.GetEventObject()
		
	def _setEventObject(self, obj):
		self.SetEventObject(obj)
	
	def _getEventData(self):
		return self._eventData
		
	def _setEventData(self, dict):
		self._eventData = dict
	
	EventObject = property(_getEventObject, _setEventObject, None, 
		"References the object that emitted the event.")
		
	EventData = property(_getEventData, _setEventData, None,
		"Dictionary of data name/value pairs associated with the event.")
		

class dEvent(wx.PyEvent, dEventBase):
	def __init__(self, eventType, eventObject, _nativeEvent=None):
		wx.PyEvent.__init__(self)
		dEventBase.__init__(self, eventType, eventObject, _nativeEvent)
		
class dCommandEvent(wx.PyCommandEvent, dEventBase):
	def __init__(self, eventType, eventObject, _nativeEvent=None):
		wx.PyCommandEvent.__init__(self)
		dEventBase.__init__(self, eventType, eventObject, _nativeEvent)
