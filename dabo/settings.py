# Dabo Global Settings

# Do not modify this file directly. Instead, create a file called 
# settings_override.py, and copy/paste the settings section below into the 
# settings_override.py file. This way, when you update Dabo, you won't blow 
# away your custom tweaks.

# Note that creating a settings_override.py isn't the only way to tweak the 
# settings - your custom code can also just make the settings in the dabo 
# namespace at runtime, eg:
#
#  import dabo
#  dabo.eventLogging = True
#  <do stuff>
#  dabo.eventLogging = False

# Also note that settings_override.py is not the appropriate place to put 
# application-specific settings, although it may seem at first like an easy 
# place to do so.


### Settings - begin

# Event logging is turned off globally by default for performance reasons.
# Set to True (and also set LogEvents on the object(s)) to get logging.
eventLogging = False

# Set the following to True to get all the data in the UI event put into
# the dEvent EventData dictionary. Only do that for testing, though,
# because it is very expensive from a performance standpoint.
allNativeEventInfo = False

# Set dabo.fastNameSet to True to bypass Dabo's checking to make sure siblings
# have unique names, greatly speeding up instantiation of many objects. If you
# do this, your code takes responsibility for ensuring that sibling names are
# in fact unique. We recommend you leave fastNameSet to False here, and wrap 
# your object creations around setting it to True. eg:
#
#   dabo.fastNameSet = True
#   for i in range(200):
#     self.addObject(dabo.ui.dButton, Name="b_%s" % i)
#   dabo.fastNameSet = False
fastNameSet = False


# dabo.autoBindEvents is a global flag which determines if events are bound
# automatically to callback functions when the object is instantiated. E.g.,
# where you used to have to have code like:
#
#   def initEvents(self):
#       self.bindEvent(dEvents.MouseEnter, self.onMouseEnter)
#
# with autoBindEvents, all you need to do is define the onMouseEnter function,
# and Dabo will understand that that function should be called upon the
# MouseEnter event. Additionally, if an object has it's RegID set, the form
# can have callbacks of the form on<EventName>_<ObjectName>(), which become
# the callback function for that event and object. E.g.:
#
#   def onMouseEnter_cmdOkay(self, evt):
#       """This gets called when the mouse enters the okay command button."""
#
autoBindEvents = True


### Settings - end

# Do not copy/paste anything below this line into settings_override.py.

try:
	from settings_override import *
except ImportError:
	pass
