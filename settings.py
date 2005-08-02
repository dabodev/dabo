# Dabo Global Settings

# Do not modify this file directly. Instead, create a file called 
# settings_override.py, and copy/paste the settings section below 
# into the settings_override.py file. This way, when you update 
# Dabo, you won't blow away your custom tweaks.

# Note that creating a settings_override.py isn't the only way
# to tweak the settings - your custom code can also just make the
# settings in the dabo namespace at runtime, eg:
#
#  import dabo
#  dabo.eventLogging = True
#  <do stuff>
#  dabo.eventLogging = False

# Also note that settings_override.py is not the appropriate place
# to put application-specific settings, although it may seem at
# first like an easy place to do so.


### Settings - begin

# Event logging is turned off globally by default for performance reasons.
# Set to True (and also set LogEvents on the object(s)) to get logging.
eventLogging = False

# Set the following to True to get all the data in the UI event put into
# the dEvent EventData dictionary. Only do that for testing, though,
# because it is very expensive from a performance standpoint.
allNativeEventInfo = False

### Settings - end

# Do not copy/paste anything below this line into settings_override.py.

try:
	from settings_override import *
except ImportError:
	pass
