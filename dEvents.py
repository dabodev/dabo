import time
import dabo
from dabo.common import dObject

class Event(dObject):
	""" Base class for Dabo events.
	
	Event objects are instantiated in self.raiseEvent(), and passed to all 
	callbacks registered with self.bindEvent().
	
	User code can define custom events by simply subclassing Event and then 
	using self.bindEvent() and self.raiseEvent() in your objects.
	"""		
	def __init__(self, eventObject, uiEvent=None, *args, **kwargs):
		#Event.doDefault()
		super(Event, self).__init__()
		
		self.EventObject = eventObject
		self._uiEvent = uiEvent
		self._args = args
		self._kwargs = kwargs
		
		self._baseClass = Event
		
		self._insertEventData()
		self._logEvent()
		

	def stop(self):
		"""Stop the event from being handled by other handlers.
		
		This is an alternative to setting the Continue property to False.
		"""
		self.Continue = False
		
		
	def _insertEventData(self):
		""" Place ui-specific stuff into the ui-agnostic EventData dictionary.
		"""
		self._extraLogInfo = ""
		self.EventData = {}		
		ne = self._uiEvent
		
		self.EventData["timestamp"] = time.localtime()

		# Add any keyword args passed:
		for key in self._kwargs.keys():
			self.EventData[key] = self._kwargs[key]

		# Add native event data:
		if ne is not None:
			# Each UI lib should implement getEventData()
			uiEventData = dabo.ui.getEventData(ne)
			
			for key in uiEventData.keys():
				self.EventData[key] = uiEventData[key]
				
			if isinstance(self, KeyEvent):
				self._extraLogInfo = "KeyCode: %s  KeyChar: %s" % (self.EventData["keyCode"], 
					self.EventData["keyChar"])

			if isinstance(self, MouseEvent):
				self._extraLogInfo = "X:%s Y:%s" % (self.EventData["mousePosition"][0], 
					self.EventData["mousePosition"][1])
				
			
	def _logEvent(self):
		""" Log the event if the event object's LogEvents property is set.
		"""
		eventName = self.__class__.__name__
		
		try:
			logEvents = self._eventObject.LogEvents
		except AttributeError:
			logEvents = []
		noLogEvents = []
		
		if len(logEvents) > 0 and logEvents[0].lower() == "all":
			# If there are any events listed explicitly, those must not be
			# logged.
			noLogEvents = logEvents[1:]

		if eventName not in noLogEvents:		
			for logEventName in logEvents:
				if logEventName.lower() == "all" or logEventName == eventName:
					dabo.infoLog.write("dEvent Fired: %s.%s %s" % (self._eventObject.getAbsoluteName(), 
						self.__class__.__name__,
						self._extraLogInfo))
					break

	def __getattr__(self, att):
		return getattr(self._uiEvent, att)

	def _getContinue(self):
		try:
			v = self._continue
		except AttributeError:
			v = True
		return v
		
	def _setContinue(self, val):
		self._continue = bool(val)
		
	def _getEventObject(self):
		return self._eventObject
		
	def _setEventObject(self, obj):
		self._eventObject = obj
	
	def _getEventData(self):
		return self._eventData
		
	def _setEventData(self, dict):
		self._eventData = dict
	
	Continue = property(_getContinue, _setContinue, None,
		"Specifies whether the event is allowed to continue on to the next handler.")
		
	EventObject = property(_getEventObject, _setEventObject, None, 
		"References the object that emitted the event.")
		
	EventData = property(_getEventData, _setEventData, None,
		"Dictionary of data name/value pairs associated with the event.")
		

		
class MouseEvent(Event):
	pass
	
class KeyEvent(Event):
	pass
	
class DataEvent(Event):
	pass
	

class Activate(Event):
	"""Occurs when the form or application becomes active."""
	pass
	
class Close(Event):
	"""Occurs when the user closes the form."""
	pass
	
class Create(Event):
	"""Occurs after the control or form is created."""
	pass
	
class Deactivate(Event):
	"""Occurs when another form becomes active."""
	pass
	
class Destroy(Event):
	"""Occurs when the control or form is destroyed."""
	pass
	
class Hit(Event):
	"""Occurs with the control's default event (button click, listbox pick, checkbox, etc.)"""
	pass
	
class Idle(Event):
	"""Occurs when the event loop has no active events to process.
	
	This is a good place to put redraw or other such UI-intensive code, so that it 
	will only run when the application is otherwise not busy doing other (more 
	important) things.
	"""
	pass
	
class ItemPicked(Event):
	"""Occurs when an item was picked from a picklist."""
	pass
	
class GotFocus(Event):
	"""Occurs when the control gets the focus."""
	pass

	
class KeyChar(KeyEvent):
	"""Occurs when a key is depressed and released on the focused control or form."""
	pass
	
class KeyDown(KeyEvent):
	"""Occurs when any key is depressed on the focused control or form."""
	pass
	
class KeyUp(KeyEvent):
	"""Occurs when any key is released on the focused control or form."""
	pass

	
class LostFocus(Event):
	"""Occurs when the control loses the focus."""
	pass

class Move(Event):
	"""Occurs when the control's position changes."""
	pass
	
		
class MouseEnter(MouseEvent):
	"""Occurs when the mouse pointer enters the form or control."""
	pass
	
class MouseLeave(MouseEvent): 
	"""Occurs when the mouse pointer leaves the form or control."""
	pass
	
class MouseLeftClick(MouseEvent):
	"""Occurs when the mouse's left button is depressed and released on the control."""
	pass
	
class MouseLeftDoubleClick(MouseEvent):
	"""Occurs when the mouse's left button is double-clicked on the control."""
	pass
	
class MouseMove(MouseEvent):
	"""Occurs when the mouse moves in the control."""
	
class MouseRightClick(MouseEvent):
	"""Occurs when the mouse mouse's right button is depressed and released on the control."""
	pass
	
class MouseLeftDown(MouseEvent):
	"""Occurs when the mouse's left button is depressed on the control."""
	pass
	
class MouseLeftUp(MouseEvent):
	"""Occurs when the mouse's left button is released on the control."""
	pass
	
class MouseRightDown(MouseEvent):
	"""Occurs when the mouse's right button is depressed on the control."""
	pass
	
class MouseRightUp(MouseEvent):
	"""Occurs when the mouse's right button is released on the control."""
	pass


class Paint(Event):
	"""Occurs when it is time to paint the control."""
	pass
	
class PageEnter(Event):
	"""Occurs when the page becomes the active page."""
	pass
	
class PageLeave(Event):
	"""Occurs when a different page becomes active."""
	pass


class Resize(Event):
	"""Occurs when the control or form is resized."""
	pass
	
		
class RowNumChanged(DataEvent):
	"""Occurs when the cursor's row number has changed."""
	pass

class ValueRefresh(Event):
	"""Occurs when the form wants the controls to refresh their values."""
	pass

