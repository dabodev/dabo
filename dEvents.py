import time
import dabo
from dabo.dObject import dObject
import dabo.ui as ui
import dabo.biz.dBizobj as dBizobj

class Event(dObject):
	""" Base class for Dabo events.
	
	Event objects are instantiated in self.raiseEvent(), and passed to all 
	callbacks registered with self.bindEvent().
	
	User code can define custom events by simply subclassing Event and then 
	using self.bindEvent() and self.raiseEvent() in your objects.
	"""		
	def __init__(self, eventObject, uiEvent=None, *args, **kwargs):
		# Event objects get instantiated with every single event, so try
		# to keep code to a minimum here.
		
		# There isn't any superclass init code, so don't run it
		#super(Event, self).__init__()
		
		self._eventObject = eventObject
		self._uiEvent = uiEvent
		self._args = args
		self._kwargs = kwargs
		self._continue = True
		
		self._baseClass = Event
		
		self._insertEventData()
		
		if dabo.eventLogging:
			self._logEvent()
		
	
	def appliesToClass(eventClass, objectClass):
		""" Returns True if this event can be raised by the passed class.
		
		Stub: subclass events need to override with appropriate logic.
		"""
		return False
	appliesToClass = classmethod(appliesToClass)
			
		
	def stop(self):
		"""Stop the event from being handled by other handlers.
		
		This is an alternative to setting the Continue property to False.
		"""
		self.Continue = False
		
		
	def _insertEventData(self):
		""" Place ui-specific stuff into the ui-agnostic EventData dictionary.
		"""
		eventData = {}		
		nativeEvent = self._uiEvent
		kwargs = self._kwargs
		
		eventData["timestamp"] = time.localtime()

		# Add any keyword args passed:
		for key in kwargs.keys():
			eventData[key] = kwargs[key]

		# Add native event data:
		if nativeEvent is not None:
			# Each UI lib should implement getEventData()
			uiEventData = dabo.ui.getEventData(nativeEvent)
			
			for key in uiEventData.keys():
				eventData[key] = uiEventData[key]
				
		self._eventData = eventData				
				
			
	def _logEvent(self):
		""" Log the event if the event object's LogEvents property is set.
		"""
		eventName = self.__class__.__name__
		
		try:
			logEvents = self._eventObject._getLogEvents()
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
					dabo.infoLog.write("dEvent Fired: %s %s" % (self._eventObject.getAbsoluteName(), 
						self.__class__.__name__,))
					break

	def __getattr__(self, att):
		if self._eventData.has_key(att):
			return self._eventData[att]
		return None
			
	def _getContinue(self):
		return self._continue
		
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
		

class DataEvent(Event):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.biz.dBizobj)
	appliesToClass = classmethod(appliesToClass)
			
class GridEvent(Event):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dGrid)
	appliesToClass = classmethod(appliesToClass)
	
class KeyEvent(Event):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)
	
class MenuEvent(Event):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, (dabo.ui.dMenu, dabo.ui.dMenuItem,
		                                dabo.ui.dMenuBar))
	appliesToClass = classmethod(appliesToClass)
	
class MouseEvent(Event):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)
	
class SashEvent(Event):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dSplitter)
	appliesToClass = classmethod(appliesToClass)

class TreeEvent(Event):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dTreeView)
	appliesToClass = classmethod(appliesToClass)

class ListEvent(Event):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, (dabo.ui.dListControl, dabo.ui.dListBox))
	appliesToClass = classmethod(appliesToClass)
	
class Activate(Event):
	"""Occurs when the form or application becomes active."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, (dabo.dApp, dabo.ui.dForm, dabo.ui.dFormMain, dabo.ui.dDialog))
	appliesToClass = classmethod(appliesToClass)
	
class Close(Event):
	"""Occurs when the user closes the form."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, (dabo.ui.dForm, dabo.ui.dFormMain, dabo.ui.dDialog))
	appliesToClass = classmethod(appliesToClass)
	
class Create(Event):
	"""Occurs after the control or form is created."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)
	
class ChildBorn(Event):
	"""Occurs when a child control is created."""
	def __init__(self, *args, **kwargs):
		try:
			self.Child = kwargs["child"]
		except KeyError:
			self.Child = None
		super(ChildBorn, self).__init__(*args, **kwargs)
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)

class ContextMenu(MenuEvent):
	"""Occurs when the user requests a context menu (right-click on Win, opt-click on Mac, etc."""
	pass
	
class Deactivate(Event):
	"""Occurs when another form becomes active."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, (dabo.dApp, dabo.ui.dForm, dabo.ui.dFormMain, dabo.ui.dDialog))
	appliesToClass = classmethod(appliesToClass)
	
class Destroy(Event):
	"""Occurs when the control or form is destroyed."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)
	
class Hit(Event):
	"""Occurs with the control's default event (button click, listbox pick, checkbox, etc.)"""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, (ui.dBitmapButton, ui.dButton, ui.dCheckBox,
			ui.dDropdownList, ui.dEditBox, ui.dListBox,
			ui.dRadioGroup, ui.dSlider, ui.dSpinner, ui.dTextBox,
			ui.dTimer, ui.dToggleButton, ui.dMenuItem))
	appliesToClass = classmethod(appliesToClass)
	
class Idle(Event):
	"""Occurs when the event loop has no active events to process.
	
	This is a good place to put redraw or other such UI-intensive code, so that it 
	will only run when the application is otherwise not busy doing other (more 
	important) things.
	"""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)
	
class GotFocus(Event):
	"""Occurs when the control gets the focus."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)

	
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
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)


class MenuHighlight(MenuEvent):
	"""Occurs when a menu item is highlighted."""
	pass


class Move(Event):
	"""Occurs when the control's position changes."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)
	
		
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
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)
	
class PageEnter(Event):
	"""Occurs when the page becomes the active page."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPage)
	appliesToClass = classmethod(appliesToClass)
	
class PageLeave(Event):
	"""Occurs when a different page becomes active."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPage)
	appliesToClass = classmethod(appliesToClass)


class Resize(Event):
	"""Occurs when the control or form is resized."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)
	
		
class RowNumChanged(DataEvent):
	"""Occurs when the cursor's row number has changed."""
	pass

	
class SashDoubleClick(SashEvent):
	"""Occurs when a user double-clicks on the sash of a splitter window."""
	pass

class ListSelection(ListEvent):
	""" Occurs when an item is highlighted in a list."""
	pass

class ListDeselection(ListEvent):
	""" Occurs when a selected item is deselected in a list."""
	pass

class TreeSelection(TreeEvent):
	""" Occurs when the selected item in a tree control changes."""
	pass

class TreeItemCollapse(TreeEvent):
	""" Occurs when an expanded item in a tree collapses."""
	pass

class TreeItemExpand(TreeEvent):
	""" Occurs when a collapsed item in a tree expands."""
	pass

class GridContextMenu(GridEvent, MenuEvent):
	"""Occurs when the context menu is requested in the grid region."""
	pass

class GridHeaderContextMenu(GridEvent, MenuEvent):
	"""Occurs when the context menu is requested in the grid header region."""
	pass

class GridHeaderIdle(GridEvent):
	"""Occurs when an idle cycle happens in the grid header."""
	pass

class GridHeaderMouseEnter(GridEvent, MouseEvent):
	"""Occurs when the mouse pointer enters the grid's header region."""
	pass

class GridHeaderMouseLeave(GridEvent, MouseEvent):
	"""Occurs when the mouse pointer leaves the grid's header region."""
	pass

class GridHeaderMouseLeftClick(GridEvent, MouseEvent):
	"""Occurs when the left mouse button is clicked in the header region."""
	pass

class GridHeaderMouseLeftDoubleClick(GridEvent, MouseEvent):
	"""Occurs when the left mouse button is double-clicked in the header region."""
	pass

class GridHeaderMouseLeftDown(GridEvent, MouseEvent):
	"""Occurs when the left mouse button goes down in the header region."""
	pass

class GridHeaderMouseLeftUp(GridEvent, MouseEvent):
	"""Occurs when the left mouse button goes up in the header region."""
	pass

class GridHeaderMouseRightClick(GridEvent, MouseEvent):
	"""Occurs when the right mouse button is clicked in the header region."""
	pass

class GridHeaderMouseRightDown(GridEvent, MouseEvent):
	"""Occurs when the left mouse button goes down in the header region."""
	pass

class GridHeaderMouseRightUp(GridEvent, MouseEvent):
	"""Occurs when the left mouse button goes up in the header region."""
	pass

class GridHeaderMouseMove(GridEvent, MouseEvent):
	"""Occurs when the mouse moves in the grid header region."""
	pass

class GridHeaderPaint(GridEvent):
	"""Occurs when it's time to paint the grid header."""
	pass

class GridMouseLeftClick(GridEvent, MouseEvent):
	"""Occurs when the left mouse button is clicked in the grid region."""
	pass

class GridMouseLeftDoubleClick(GridEvent, MouseEvent):
	"""Occurs when the left mouse button is double-clicked in the grid region."""
	pass

class GridMouseLeftDown(GridEvent, MouseEvent):
	"""Occurs when the left mouse button goes down in the grid region."""
	pass

class GridMouseLeftUp(GridEvent, MouseEvent):
	"""Occurs when the left mouse button goes up in the grid region."""
	pass

class GridMouseRightClick(GridEvent, MouseEvent):
	"""Occurs when the right mouse button is clicked in the header region."""
	pass

class GridMouseRightDown(GridEvent, MouseEvent):
	"""Occurs when the right mouse button goes down in the grid region."""
	pass

class GridMouseRightUp(GridEvent, MouseEvent):
	"""Occurs when the right mouse button goes up in the grid region."""
	pass

class GridMouseMove(GridEvent, MouseEvent):
	"""Occurs when the mouse moves in the grid region (not the headers)."""
	pass

class GridRowSize(GridEvent):
	"""Occurs when the grid's rows are resized."""
	pass

class GridCellSelected(GridEvent):
	"""Occurs when the a new cell is selected in the grid."""
	pass

class GridCellEdited(GridEvent):
	"""Occurs when the user edits the content of a grid cell."""
	pass

class GridColSize(GridEvent):
	"""Occurs when the grid's columns are resized."""
	pass


	
class ValueChanged(Event):
	"""Occurs when the control's value has changed, whether programmatically or interactively."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dDataControlMixin)
	appliesToClass = classmethod(appliesToClass)
	
class ValueRefresh(Event):
	"""Occurs when the form wants the controls to refresh their values."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dForm)
	appliesToClass = classmethod(appliesToClass)

