# -*- coding: utf-8 -*-
import logging
import time
import dabo
from dabo.dLocalize import _

class dEvent(object):
	""" Base class for Dabo events.

	Event objects are instantiated in self.raiseEvent(), and passed to all
	callbacks registered with self.bindEvent().

	User code can define custom events by simply subclassing Event and then
	using self.bindEvent() and self.raiseEvent() in your objects.
	"""
	def __init__(self, eventObject, uiEvent=None, eventData=None, *args, **kwargs):
		# Event objects get instantiated with every single event, so try
		# to keep code to a minimum here.
		#super(dEvent, self).__init__(*args, **kwargs)

		self._eventObject = eventObject
		self._uiEvent = uiEvent
		self._args = args
		self._kwargs = kwargs
		self._continue = True
		self._baseClass = dEvent

		self._insertEventData()
		if eventData:
			self._eventData.update(eventData)

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
		""" Place ui-specific stuff into the ui-agnostic EventData dictionary."""
		eventData = {}
		nativeEvent = self._uiEvent
		kwargs = self._kwargs

		eventData["timestamp"] = time.localtime()

		# Add any keyword args passed:
		for key in kwargs:
			eventData[key] = kwargs[key]

		# Add native event data:
		if nativeEvent is not None:
			# Each UI lib should implement getEventData()
			uiEventData = dabo.ui.getEventData(nativeEvent)

			for key in uiEventData:
				eventData[key] = uiEventData[key]

		self._eventData = eventData


	def _logEvent(self):
		""" Log the event if the event object's LogEvents property is set."""
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
					holdLevel = dabo.log.level
					dabo.log.setLevel(logging.INFO)
					dabo.log.info("dEvent Fired: %s %s" %
							(self._eventObject,
							self.__class__.__name__,))
					dabo.log.setLevel(holdLevel)
					break


	def __getattr__(self, att):
		try:
			return self._eventData[att]
		except KeyError:
			raise AttributeError("%s.%s object has no attribute %s." % (
					self.__class__.__module__, self.__class__.__name__, att))


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
			_("""Specifies whether the event is allowed to continue
			on to the next handler.  (bool)"""))

	EventObject = property(_getEventObject, _setEventObject, None,
			_("References the object that emitted the event.  (obj)"""))

	EventData = property(_getEventData, _setEventData, None,
			_("""Dictionary of data name/value pairs associated
			with the event.  (dict)"""))

# Eventually deprecate Event
Event=dEvent

class DataEvent(dEvent):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.biz.dBizobj)
	appliesToClass = classmethod(appliesToClass)


class EditorEvent(dEvent):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dEditor)
	appliesToClass = classmethod(appliesToClass)


class GridEvent(dEvent):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dGrid)
	appliesToClass = classmethod(appliesToClass)


class KeyEvent(dEvent):
	def appliesToClass(eventClass, objectClass):
		from dabo.dApp import dApp
		return issubclass(objectClass, (dabo.ui.dPemMixin, dApp))
	appliesToClass = classmethod(appliesToClass)


class ListControlEvent(dEvent):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, (dabo.ui.dListControl, ))
	appliesToClass = classmethod(appliesToClass)


class MenuEvent(dEvent):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, (dabo.ui.dMenu, dabo.ui.dMenuItem,
				dabo.ui.dMenuBar))
	appliesToClass = classmethod(appliesToClass)


class MouseEvent(dEvent):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)


class ControlNavigationEvent(dEvent):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, (dabo.ui.dPage, dabo.ui.dForm))
	appliesToClass = classmethod(appliesToClass)


class SashEvent(dEvent):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dSplitter)
	appliesToClass = classmethod(appliesToClass)


class CalendarEvent(dEvent):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dCalendar)
	appliesToClass = classmethod(appliesToClass)


class TreeEvent(dEvent):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dTreeView)
	appliesToClass = classmethod(appliesToClass)


class SpinnerEvent(dEvent):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dSpinner)
	appliesToClass = classmethod(appliesToClass)


class ReportEvent(dEvent):
	def appliesToClass(eventClass, objectClass):
		try:
			return issubclass(objectClass, dabo.dReportWriter.dReportWriter)
		except AttributeError:
			# dReportWriter not loaded, so it doesn't apply
			return False
	appliesToClass = classmethod(appliesToClass)


class ScrollEvent(dEvent):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, (dabo.ui.dScrollPanel, dabo.ui.dGrid))
	appliesToClass = classmethod(appliesToClass)


class MediaEvent(dEvent):
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dMediaControl)
	appliesToClass = classmethod(appliesToClass)


class Activate(dEvent):
	"""Occurs when the form or application becomes active."""
	def appliesToClass(eventClass, objectClass):
		from dabo.dApp import dApp
		return issubclass(objectClass, (dApp, dabo.ui.dForm,
				dabo.ui.dFormMain, dabo.ui.dDialog))
	appliesToClass = classmethod(appliesToClass)


class Close(dEvent):
	"""Occurs when the user closes the form."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, (dabo.ui.dForm, dabo.ui.dFormMain,
				dabo.ui.dDialog))
	appliesToClass = classmethod(appliesToClass)


class Create(dEvent):
	"""Occurs after the control or form is created."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)


class ChildBorn(dEvent):
	"""Occurs when a child control is created."""
	def __init__(self, *args, **kwargs):
		try:
			self.Child = kwargs["child"]
		except KeyError:
			self.Child = None
		super(ChildBorn, self).__init__(*args, **kwargs)
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, (dabo.ui.dForm, dabo.ui.dDialog,
				dabo.ui.dPanel, dabo.ui.dPage, dabo.ui.dPageFrame, dabo.ui.dPageStyled,
				dabo.ui.dPageList, dabo.ui.dPageSelect, dabo.ui.dPageFrameNoTabs))
	appliesToClass = classmethod(appliesToClass)


class ContextMenu(dEvent):
	"""Occurs when the user requests a context menu (right-click on Win,
	control-click on Mac, etc.
	"""
	pass


class Deactivate(dEvent):
	"""Occurs when another form becomes active."""
	def appliesToClass(eventClass, objectClass):
		from dabo.dApp import dApp
		return issubclass(objectClass, (dApp, dabo.ui.dForm,
				dabo.ui.dFormMain, dabo.ui.dDialog))
	appliesToClass = classmethod(appliesToClass)


class Destroy(dEvent):
	"""Occurs when the control or form is destroyed."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)


class FontPropertiesChanged(dEvent):
	"""Occurs when the properties of a dFont have changed."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)


class Hit(dEvent):
	"""Occurs with the control's default event (button click,
	listbox pick, checkbox, etc.)
	"""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, (dabo.ui.dBitmapButton, dabo.ui.dButton,
				dabo.ui.dCheckBox, dabo.ui.dComboBox, dabo.ui.dDropdownList,
				dabo.ui.dEditBox, dabo.ui.dListBox, dabo.ui.dRadioList,
				dabo.ui.dSlider, dabo.ui.dSpinner, dabo.ui.dTextBox, dabo.ui.dTimer,
				dabo.ui.dToggleButton, dabo.ui.dMenuItem, dabo.ui.dToolBarItem))
	appliesToClass = classmethod(appliesToClass)


class Idle(dEvent):
	"""Occurs when the event loop has no active events to process.

	This is a good place to put redraw or other such UI-intensive code, so that it
	will only run when the application is otherwise not busy doing other (more
	important) things.
	"""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)


class GotFocus(dEvent):
	"""Occurs when the control gets the focus."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)


class KeyChar(KeyEvent):
	"""Occurs when a key is depressed and released on the
	focused control or form.
	"""
	pass


class KeyDown(KeyEvent):
	"""Occurs when any key is depressed on the focused control or form."""
	pass


class KeyUp(KeyEvent):
	"""Occurs when any key is released on the focused control or form."""
	pass


class LostFocus(dEvent):
	"""Occurs when the control loses the focus."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)


class MenuHighlight(MenuEvent):
	"""Occurs when a menu item is highlighted."""
	pass


class MenuOpen(MenuEvent):
	"""Occurs when a menu is about to be opened."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)


class MenuClose(MenuEvent):
	"""Occurs when a menu has just been closed."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)


class Move(dEvent):
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


class MouseMove(MouseEvent):
	"""Occurs when the mouse moves in the control."""
	pass


class MouseWheel(MouseEvent):
	"""Occurs when the user scrolls the mouse wheel."""
	pass


class MouseLeftDown(MouseEvent):
	"""Occurs when the mouse's left button is depressed on the control."""
	pass


class MouseLeftUp(MouseEvent):
	"""Occurs when the mouse's left button is released on the control."""
	pass


class MouseLeftClick(MouseEvent):
	"""Occurs when the mouse's left button is depressed
	and released on the control.
	"""
	pass


class MouseLeftDoubleClick(MouseEvent):
	"""Occurs when the mouse's left button is double-clicked on the control."""
	pass


class MouseRightDown(MouseEvent):
	"""Occurs when the mouse's right button is depressed on the control."""
	pass


class MouseRightUp(MouseEvent):
	"""Occurs when the mouse's right button is released on the control."""
	pass


class MouseRightClick(MouseEvent):
	"""Occurs when the mouse mouse's right button is depressed
	and released on the control.
	"""
	pass


class MouseRightDoubleClick(MouseEvent):
	"""Occurs when the mouse's right button is double-clicked on the control."""
	pass


class MouseMiddleDown(MouseEvent):
	"""Occurs when the mouse's middle button is depressed on the control."""
	pass


class MouseMiddleUp(MouseEvent):
	"""Occurs when the mouse's middle button is released on the control."""
	pass


class MouseMiddleClick(MouseEvent):
	"""Occurs when the mouse mouse's middle button is depressed
	and released on the control.
	"""
	pass


class MouseMiddleDoubleClick(MouseEvent):
	"""Occurs when the mouse's middle button is double-clicked
	on the control.
	"""
	pass


class Paint(dEvent):
	"""Occurs when it is time to paint the control."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)


class BackgroundErased(dEvent):
	"""Occurs when a window background has been erased and needs repainting."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)


class PageChanged(dEvent):
	"""Occurs when a page in a pageframe-like control changes"""
	def appliesToClass(eventClass, objectClass):
		try:
			return issubclass(objectClass, (dabo.ui.dPageFrame, dabo.ui.dPageList,
					dabo.ui.dPageSelect, dabo.ui.dPageFrameNoTabs, dabo.ui.dPageStyled))
		except AttributeError:
			return issubclass(objectClass, (dabo.ui.dPageFrame, dabo.ui.dPageList,
					dabo.ui.dPageSelect, dabo.ui.dPageFrameNoTabs))
	appliesToClass = classmethod(appliesToClass)


class PageChanging(dEvent):
	"""Occurs when the current page in a pageframe-like control is about to change"""
	def appliesToClass(eventClass, objectClass):
		try:
			return issubclass(objectClass, (dabo.ui.dPageFrame, dabo.ui.dPageList,
					dabo.ui.dPageSelect, dabo.ui.dPageFrameNoTabs, dabo.ui.dPageStyled))
		except AttributeError:
			return issubclass(objectClass, (dabo.ui.dPageFrame, dabo.ui.dPageList,
					dabo.ui.dPageSelect, dabo.ui.dPageFrameNoTabs))
	appliesToClass = classmethod(appliesToClass)


class PageClosed(dEvent):
	"""Occurs when a page in a dPageStyled control is closed"""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPageStyled)
	appliesToClass = classmethod(appliesToClass)


class PageClosing(dEvent):
	"""Occurs when a page in a dPageStyled control is about to close"""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPageStyled)
	appliesToClass = classmethod(appliesToClass)


class PageContextMenu(dEvent):
	"""Occurs when the user requests a context event for a dPage"""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPage)
	appliesToClass = classmethod(appliesToClass)


class PageEnter(dEvent):
	"""Occurs when the page becomes the active page."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPage)
	appliesToClass = classmethod(appliesToClass)


class PageLeave(dEvent):
	"""Occurs when a different page becomes active."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPage)
	appliesToClass = classmethod(appliesToClass)


class Resize(dEvent):
	"""Occurs when the control or form is resized."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)


class SearchButtonClicked(dEvent):
	"""Occurs when the user clicks the search button in a dSearchBox."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, (dabo.ui.dSearchBox,))
	appliesToClass = classmethod(appliesToClass)


class SearchCancelButtonClicked(dEvent):
	"""Occurs when the user clicks the cancel button in a dSearchBox."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, (dabo.ui.dSearchBox,))
	appliesToClass = classmethod(appliesToClass)


class SlidePanelChange(dEvent):
	"""Occurs when a panel in a dSlidePanelControl control is hidden or shown."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, (dabo.ui.dSlidePanelControl, dabo.ui.dSlidePanel))
	appliesToClass = classmethod(appliesToClass)


class SlidePanelCaptionClick(dEvent):
	"""Occurs when the caption bar of a dSlidePanel is clicked."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, (dabo.ui.dFoldPanelBar, dabo.ui.dSlidePanel))
	appliesToClass = classmethod(appliesToClass)


class RowNumChanged(DataEvent):
	"""Occurs when the RowNumber of the PrimaryBizobj of the dForm has changed."""
	pass

class RowNavigation(DataEvent):
	"""Occurs when the PrimaryBizobj of the dForm is being navigated.

	As the user is rapidly calling dForm.next(), .prior(), etc., RowNavigation
	events get raised. Your code should do some quick display updates to indicate
	to the user that the record is changing, but the child bizobj's won't be
	requeried until after the navigation has ended.

	See also RowNumChanged, which only occurs after the user has settled on a
	record and has stopped navigating.
	"""
	pass

class SashDoubleClick(SashEvent):
	"""Occurs when a user double-clicks on the sash of a splitter window."""
	pass


class SashPositionChanged(SashEvent):
	"""Occurs when a user moves the sash of a splitter window."""
	pass


class CalendarDateChanged(CalendarEvent):
	"""Occurs when the date on a calendar is changed."""
	pass


class CalendarDayChanged(CalendarEvent):
	"""Occurs when the day of the month on a calendar is changed."""
	pass


class CalendarMonthChanged(CalendarEvent):
	"""Occurs when the month on a calendar is changed."""
	pass


class CalendarYearChanged(CalendarEvent):
	"""Occurs when the year on a calendar is changed."""
	pass


class CalendarDayHeaderClicked(CalendarEvent):
	"""Occurs when the day of week header is clicked."""
	pass


class ListSelection(ListControlEvent):
	""" Occurs when an item is highlighted in a list control."""
	pass


class ListDeselection(ListControlEvent):
	""" Occurs when a selected item is deselected in a list control."""
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


class TreeItemContextMenu(TreeEvent):
	""" Occurs when a tree item receives a context menu event."""
	pass


class TreeBeginDrag(MouseEvent):
	""" Occurs when a drag operation begins in a tree."""
	pass


class TreeEndDrag(MouseEvent):
	""" Occurs when a drag operation ends in a tree."""
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


class GridRangeSelected(GridEvent):
	"""Occurs when the a new cell is selected in the grid."""
	pass


class GridCellEditBegin(GridEvent):
	"""Occurs when the editor for a grid cell is shown, allowing the user to edit."""
	pass


class GridCellEditEnd(GridEvent):
	"""Occurs when the editor for a grid cell is hidden."""
	pass


class GridCellEdited(GridEvent):
	"""Occurs when the user edits the content of a grid cell."""
	pass


class GridCellEditorHit(GridEvent):
	"""Occurs when the user changes the value in the grid cell editor.

	For a checkbox, this occurs when the user toggles the checkmark.
	This event is not implemented for other grid cell editors, yet.
	"""
	pass


class GridColSize(GridEvent):
	"""Occurs when the grid's columns are resized."""
	pass


class GridBeforeSort(GridEvent):
	"""Occurs before the grid is sorted"""
	pass


class GridAfterSort(GridEvent):
	"""Occurs after the grid is sorted"""
	pass


class ListHeaderMouseLeftClick(GridEvent, MouseEvent):
	"""Occurs when the left mouse button is clicked in the header region of dListControl."""
	pass


class ListHeaderMouseRightClick(GridEvent, MouseEvent):
	"""Occurs when the right mouse button is clicked in the header region of dListControl."""
	pass


class ListColumnResize(GridEvent, MouseEvent):
	"""Occurs when the user manually resizes a column of dListControl."""
	pass


class DocumentationHint(EditorEvent):
	"""Occurs when the editor wants documentation information to change.

	The IDE can bind to this to direct detailed documentation into a separate
	window, likely replacing previous documentation. The user can choose how
	to display that window, if at all.

	Raise this event with three additional keyword arguments:
		+ shortDoc: a one-liner call tip
		+ longDoc: a multi-line call tip plus expanded documentation
		+ object: a reference to the object to be documented, in case
			the listener wants to format additional information about
			the object.
	"""
	pass


class TitleChanged(EditorEvent):
	"""Occurs when the editor's title changes."""
	pass


class ContentChanged(EditorEvent):
	"""Occurs when the contents of the Editor are modified."""
	pass


class EditorStyleNeeded(EditorEvent):
	"""Occurs when the underlying editor control requires restyling."""
	pass


class ValueChanged(dEvent):
	"""Occurs when the control's value has changed, whether
	programmatically or interactively.
	"""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dDataControlMixin)
	appliesToClass = classmethod(appliesToClass)

class InteractiveChange(dEvent):
	"""Occurs when the user interactively changes the control's value."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dDataControlMixin)
	appliesToClass = classmethod(appliesToClass)


class Update(dEvent):
	"""Occurs when a container wants its controls to update
	their properties.
	"""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dPemMixin)
	appliesToClass = classmethod(appliesToClass)


class HtmlLinkClicked(dEvent):
	"""Occurs when a link in a dHtmlBox control is clicked."""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dHtmlBox)
	appliesToClass = classmethod(appliesToClass)


class SpinUp(SpinnerEvent):
	"""Occurs when the spinner is incremented, either by clicking
	the spinner 'up' button or by using the keyboard up arrow.
	"""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dSpinner)
	appliesToClass = classmethod(appliesToClass)


class SpinDown(SpinnerEvent):
	"""Occurs when the spinner is decremented, either by clicking
	the spinner 'down' button or by using the keyboard down arrow.
	"""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dSpinner)
	appliesToClass = classmethod(appliesToClass)


class Spinner(SpinnerEvent):
	"""Occurs when the spinner is changed, either by clicking
	one of the spinner buttons or by using the keyboard arrows.
	"""
	def appliesToClass(eventClass, objectClass):
		return issubclass(objectClass, dabo.ui.dSpinner)
	appliesToClass = classmethod(appliesToClass)


class ReportCancel(ReportEvent):
	"""Occurs when the user cancels the report."""
	pass

class ReportBegin(ReportEvent):
	"""Occurs at the beginning of the report."""
	pass


class ReportEnd(ReportEvent):
	"""Occurs at the end of the report."""
	pass


class ReportIteration(ReportEvent):
	"""Occurs when the RecordNumber changes at report runtime."""
	pass


class ScrollTop(ScrollEvent):
	"""Occurs when a scrollable window reaches the top or left."""
	pass


class ScrollBottom(ScrollEvent):
	"""Occurs when a scrollable window reaches the bottom or right."""
	pass


class ScrollLineUp(ScrollEvent):
	"""Occurs when a scrollable window is scrolled a line up or left."""
	pass


class ScrollLineDown(ScrollEvent):
	"""Occurs when a scrollable window is scrolled a line down or right."""
	pass


class ScrollPageUp(ScrollEvent):
	"""Occurs when a scrollable window is scrolled up or left by a full page."""
	pass


class ScrollPageDown(ScrollEvent):
	"""Occurs when a scrollable window is scrolled down or right by a full page."""
	pass


class ScrollThumbDrag(ScrollEvent):
	"""Occurs when the 'thumb' control of a scrollable window's scrollbars is moved."""
	pass


class ScrollThumbRelease(ScrollEvent):
	"""Occurs when the 'thumb' control of a scrollable window's scrollbars is released."""
	pass


class MediaFinished(MediaEvent):
	"""Occurs when the media has finished playing."""
	pass


class MediaLoaded(MediaEvent):
	"""Occurs when the media has been successfully loaded."""
	pass


class MediaPause(MediaEvent):
	"""Occurs when playback has been paused."""
	pass


class MediaPlay(MediaEvent):
	"""Occurs when playback has begun."""
	pass


class MediaStop(MediaEvent):
	"""Occurs when playback has been stopped."""
	pass


class MediaStateChanged(MediaEvent):
	"""Occurs when the playback status has changed from one state to another."""
	pass


class ShellCommandRun(dEvent):
	"""Occurs when the dShell interpreter executes a command."""
	pass
