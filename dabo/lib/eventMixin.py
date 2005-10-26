import string
import types
import traceback
import dabo
from dabo.dLocalize import _


class EventMixin(object):
	"""Mix-in class making objects know how to bind and raise Dabo events.

	All Dabo objects inherit this functionality.	
	"""
	def __init__(self, *args, **kwargs):
		self._autoBindEvents(context=self)

	def bindEvent(self, eventClass, function):
		"""Bind a dEvent to a callback function.
		"""
		eb = self._EventBindings
		if (eventClass, function) not in eb:
			eb.append((eventClass, function))
		

	def bindEvents(self, bindings):
		"""Bind a sequence of [dEvent, callback] lists.
		"""
		if isinstance(bindings, (list, tuple)):
			for binding in bindings:
				self.bindEvent(binding[0], binding[1])
		else:
			raise TypeError, "Sequence expected."
		

	def raiseEvent(self, eventClass, uiEvent=None, uiCallAfterFunc=None, 
			*args, **kwargs):
		"""Send the event to all registered listeners.
		
		If uiEvent is sent, dEvents.Event will be able to parse it for useful
		information to send along to the callback. If uiCallAfterFunc is sent, the
		callbacks will be wrapped in that function so that the UI-lib can process
		our Dabo events at next idle instead of immediately in this event cycle.
		
		Additional arguments, if any, are sent along to the constructor	of the 
		event. While this feature exists so that UI-lib event handlers can pass 
		along information (such as the keystroke information in a key event), user 
		code may pass along additional arguments as well, which	will exist in the 
		event.EventData dictionary property.
		
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
			
			
	def unbindEvent(self, eventClass=None, function=None):
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
			eb = self._EventBindings[:]
			num = len(self._EventBindings)
			self._EventBindings = []
			newBindings = []
			for index in range(num, 0, -1):
				binding = eb.pop()
				bindingClass, bindingFunction = binding[0], binding[1]
				
				if (eventClass is None or bindingClass == eventClass) and (
					function is None or bindingFunction == function):
						# Matched: already popped off, do nothing
						pass
				else:
					# Not matched: put it back
					newBindings.append(binding)
			self._EventBindings = newBindings

	
	def autoBindEvents(self):
		"""Automatically bind any on*() methods to the associated event.

		User code only needs to define the callback, and Dabo will automatically
		set up the event binding. This will satisfy lots of common cases where 
		you want an object to respond to its own events. If you want another 
		object to respond to an event, you'll still have to manually set up that
		event binding.

		This feature is inspired by PythonCard.
		"""
		# We call _autoBindEvents for self and form, and force it because it was
		# asked for explicitly.
		self._autoBindEvents(context=self, force=True)
		try:
			form = self.Form
		except AttributeError:
			form = None
		if form is not None:
			self._autoBindEvents(context=form, force=True)


	def _autoBindEvents(self, context, force=False):
		import dabo.dEvents as dEvents

		if not (force or dabo.autoBindEvents):
			# autobinding is switched off globally
			return
		if context is None:
			# context could be None if during the setting of RegID property, 
			# self.Form evaluates to None.
			return

		regid = None
		contextText = ""
		if context != self:
			regid = self.RegID
			if regid is None or regid == "":
				return
			contextText = "_%s" % regid
						
		funcNames = [i for i in dir(context) if i[:2] == "on"]
		for funcName in funcNames:
			# if funcName is onActivate, then parsedEvtName == "Activate" and parsedRegID=""
			# if funcName is onHit_MyButton, then parsedEvtName == "Hit" and parsedRegID="MyButton":
			parsedEvtName = funcName.split("_")[0][2:]
			parsedRegID = "_".join(funcName.split("_")[1:])

			# Test to see if evt/regid matches:
			if regid is not None:
				if parsedRegID != regid:
					# This function name doesn't match self's RegID
					continue
			else:
				if len(parsedRegID) > 0:
					# This function name has a RegID attached, but self doesn't
					continue
			if parsedEvtName not in dir(dEvents):
				# The function's event name isn't recognized
				continue

			# If we got this far, we have a match. 

			# Get the object reference to the function:
			for m in context.__class__.mro():
				funcObj = None
				try:
					funcObj = m.__dict__[funcName]
					# The function is defined in this superclass: break here
					break
				except KeyError:
					# The function isn't defined here: continue the crawl up the mro
					pass

			if type(funcObj) in (types.FunctionType, types.MethodType):
					evtObj = dEvents.__dict__[parsedEvtName]
					funcObj = eval("context.%s" % funcName)  ## (can't use __class__.dict...)
					self.bindEvent(evtObj, funcObj)


	def getEventList(cls):
		"""Return a list of valid Dabo event names for this object."""
		el = cls.getValidEvents()
		el = [e.__name__ for e in el if e.__name__[0] in string.uppercase]
		el.sort()
		return el
	getEventList = classmethod(getEventList)


	def getValidEvents(cls):
		"""Returns a list of valid Dabo event classes for this object.

		The cls parameter can actually be either a class or self.
		"""
		classRef = cls
		try:
			issubclass(cls, object)
		except TypeError:
			# we are an instance, cls is self.
			classRef = cls.__class__

		import dabo.dEvents as e  # imported here to avoid circular import 
		validEvents = []
		events = [e.__dict__[evt] for evt in dir(e)]
		for evt in events:
			if type(evt) == type and issubclass(evt, e.Event):
				if evt.appliesToClass(classRef):
					validEvents.append(evt)
		return validEvents
	getValidEvents = classmethod(getValidEvents)


	# Allow for alternate capitalization (deprecated):
	unBindEvent = unbindEvent
	
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
		
