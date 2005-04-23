import traceback
import dabo
from dabo.dLocalize import _

class EventMixin(object):
	"""Mix-in class making objects know how to bind and raise Dabo events.

	All Dabo objects inherit this functionality.	
	"""
	def bindEvent(self, eventClass, function):
		"""Bind a dEvent to a callback function.
		"""
		self._EventBindings.append((eventClass, function))
		

	def bindEvents(self, bindings):
		"""Bind a sequence of [dEvent, callback] lists.
		"""
		if isinstance(bindings, (list, tuple)):
			for binding in bindings:
				self.bindEvent(binding[0], binding[1])
		else:
			raise TypeError, "Sequence expected."
		

	def raiseEvent(self, eventClass, uiEvent=None, 
	               uiCallAfterFunc=None, *args, **kwargs):
		"""Send the event to all registered listeners.
		
		If uiEvent is sent, dEvents.Event will be able to parse it for useful
		information to send along to the callback. If uiCallAfterFunc is sent, the
		callbacks will be wrapped in that function so that the UI-lib can process
		our Dabo events at next idle instead of immediately in this event cycle.
		
		Additional arguments, if any, are sent along to the constructor
		of the event. While this feature exists so that UI-lib event handlers
		can pass along information (such as the keystroke information in a
		key event), user code may pass along additional arguments as well, which
		will exist in the event.EventData dictionary property.
		
		User code need not worry too much about all these extra arguments, as in 
		most cases they'll be completely unnecessary. Just call raiseEvent() with
		the event class (dEvents.Hit, for example) as the only parameter.
		"""
		
		# Instantiate the event, no matter if there aren't any bindings: the event
		# did happen, after all, and perhaps we want to log that fact.

		# self.__raisedEvents keeps track of a possible problem identified by 
		# Vladimir. It is debug code that isn't intended to stick around.
		try: self.__raisedEvents
		except AttributeError:
			self.__raisedEvents = []
			
		eventSig = (eventClass, args, kwargs)
		if eventSig in self.__raisedEvents:
			dabo.errorLog.write("End-around call of event %s" % str(eventSig))
			#traceback.print_stack()
			return None
		else:
			self.__raisedEvents.append(eventSig)
			
		event = eventClass(self, uiEvent, *args, **kwargs)
		
		# Now iterate the bindings, and execute the callbacks:
		for binding in self._EventBindings:
			bindingClass, bindingFunction = binding[0], binding[1]
			if bindingClass == eventClass:
				if uiCallAfterFunc:
					# Use the native-UI's way to have the callback processed during
					# the next event idle cycle.
					uiCallAfterFunc(bindingFunction, event)
				else:
					# Wrap the call so that if an exception is raised in one
					# handler, the rest of the handlers still get a whack at 
					# the event. This matches the behavior as if we were using
					# the real event loop in the ui lib. This is only necessary
					# because we aren't using a uiCallAfterFunc().
					try:
						bindingFunction(event)
					except:
						traceback.print_exc()
			if not event.Continue:
				# The event handler set the Continue flag to False, specifying that
				# no more event handlers should process the event.
				break
		try:
			self.__raisedEvents.pop()
		except:
			# This is a deleted object; no need (or ability!) to do anything else.
			return
		
		if uiEvent is not None:
			# Let the UI lib know whether to do the default event behavior
			if event.Continue:
				r = dabo.ui.continueEvent(uiEvent)
			else:
				r = dabo.ui.discontinueEvent(uiEvent)
		else:
			r = None
			
		return r
			
			
	def unBindEvent(self, eventClass=None, function=None):
		""" Remove a previously registered event binding.
		
		Removes all registrations that exist for the given binding for this
		object. If event is None, all bindings for the passed function are 
		removed. If function is None, all bindings for the passed event are 
		removed. If both event and function are None, all event bindings are 
		removed.
		"""
		if eventClass is None and function is None:
			# Short-circuit: blank the entire list of _EventBindings
			self._EventBindings = []
		else:			
			# Iterate through _EventBindings and remove the appropriate ones
			for index in range(len(self._EventBindings), 0, -1):
				binding = self._EventBindings.pop()
				bindingClass, bindingFunction = binding[0], binding[1]
				
				if (eventClass is None or bindingClass == eventClass) and (
					function is None or bindingFunction == function):
						# Matched: already popped off, do nothing
						pass
				else:
					# Not matched: put it back
					self._EventBindings.append(binding)

		
	def _getEventBindings(self):
		try:
			return self._eventBindings
		except AttributeError:
			self._eventBindings = []
			return self._eventBindings
			
	def _setEventBindings(self, val):
		if isinstance(val, list):
			self._eventBindings = val
		else:
			raise ValueError, "EventBindings must be a list."
		
	_EventBindings = property(_getEventBindings, _setEventBindings, None, 
		_("The list of event bindings ([Event, callback]) for this object."))		
	

if __name__ == "__main__":

	def testFunc(event):
		print "testFunc", event
		
	class TestEvent(object):
		def __init__(self, eventObject):
			print "evtObject:", eventObject
		
	o = EventMixin()
	print "EventBindings:", o._EventBindings
	
	o.bindEvent(TestEvent, testFunc)
	print "EventBindings:", o._EventBindings

	o.raiseEvent(TestEvent)
	
	o.unBindEvent(TestEvent)
	print "EventBindings:", o._EventBindings
		
