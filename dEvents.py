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
		Event.doDefault()
		
		self.EventObject = eventObject
		self._uiEvent = uiEvent
		self._args = args
		self._kwargs = kwargs
		
		self._baseClass = Event
		
		self._insertEventData()
		self._logEvent()
		
				
	def _insertEventData(self):
		""" Place ui-specific stuff into the ui-agnostic EventData dictionary.
		"""
		self._extraLogInfo = ""
		self.EventData = {}		
		ne = self._uiEvent
		
		self.EventData["timestamp"] = time.localtime()
		
		if ne is not None:
			# Each UI lib should implement getEventData()
			uiEventData = dabo.ui.getEventData(ne)
			
			for key in uiEventData.keys():
				self.EventData[key] = uiEventData[key]
				
			if isinstance(self, KeyEvent):
				self._extraLogInfo = "KeyCode: %s RawKeyCode: %s" % (self.EventData["keyCode"], 
					self.EventData["rawKeyCode"])

			if isinstance(self, MouseEvent):
				self._extraLogInfo = "X:%s Y:%s" % (self.EventData["mousePosition"][0], 
					self.EventData["mousePosition"][1])
				
			
	def _logEvent(self):
		""" Log the event if the event object's LogEvents property is set.
		"""
		try:
			logEvents = self._eventObject.LogEvents
		except AttributeError:
			logEvents = []
		
		for eventName in logEvents:
			if eventName.lower() == "all" or eventName == self.__class__.__name__:
				dabo.infoLog.write("dEvent Fired: %s.%s %s" % (self._eventObject.getAbsoluteName(), 
					self.__class__.__name__,
					self._extraLogInfo))
				break

	def __getattr__(self, att):
		return getattr(self._uiEvent, att)

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

	
class PageEnter(Event):
	"""Occurs when the page becomes the active page."""
	pass
	
class PageLeave(Event):
	"""Occurs when a different page becomes active."""
	pass

	
class RowNumChanged(DataEvent):
	"""Occurs when the cursor's row number has changed."""
	pass

class ValueRefresh(Event):
	"""Occurs when the form wants the controls to refresh their values."""
	pass

