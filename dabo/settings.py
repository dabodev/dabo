# -*- coding: utf-8 -*-
"""
Dabo Global Settings

Do not modify this file directly. Instead, create a file called
settings_override.py, and copy/paste the settings section below into the
settings_override.py file. This way, when you update Dabo, you won't blow
away your custom tweaks.

Note that creating a settings_override.py isn't the only way to tweak the
settings - your custom code can also just make the settings in the dabo
namespace at runtime, eg::

    import dabo
    dabo.eventLogging = True
    <do stuff>
    dabo.eventLogging = False

.. note::

    settings_override.py is not the appropriate place to put
    application-specific settings, although it may seem at first like an easy
    place to do so.

"""

import functools
import importlib
import locale
import logging
import os
import sys
from pathlib import Path

### Settings - begin

# Event logging is turned off globally by default for performance reasons.
# Set to True (and also set LogEvents on the object(s)) to get logging.
eventLogging = False

# Set the following to True to get all the data in the UI event put into
# the event EventData dictionary. Only do that for testing, though,
# because it is very expensive from a performance standpoint.
allNativeEventInfo = False

# Set fastNameSet to True to bypass Dabo's checking to make sure siblings
# have unique names, greatly speeding up instantiation of many objects. If you
# do this, your code takes responsibility for ensuring that sibling names are
# in fact unique. We recommend you leave fastNameSet to False here, and wrap
# your object creations around setting it to True. eg:
#
#   dabo.fastNameSet = True
#   for i in range(200):
#     self.addObject(dui.dButton, Name="b_%s" % i)
#   dabo.fastNameSet = False
fastNameSet = False

# autoBindEvents specifies whether events are bound
# automatically to callback functions when the object is instantiated. E.g.,
# where you used to have to have code like:
#
#   def initEvents(self):
#       self.bindEvent(events.MouseEnter, self.onMouseEnter)
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

# If you set MDI to True, then dFormMain and dForm will default to being MDI
# parent and MDI child, respectively. IOW, you don't have to change your dForm
# and dFormMain subclasses to inherit from dFormChildMDI, etc., but it comes at
# the cost of being a global setting. This must be set before dui is
# imported (ie right at the top of your app). Note that you could instead choose
# to deal with MDI/SDI explicitly in your form subclasses. IOW:
#        class MyForm(dui.dFormChildMDI)
#        class MyForm(dui.dFormParentMDI)
#        class MyForm(dui.dFormSDI)
#
# All the MDI setting does is make dFormMain == (dFormMainSDI or dFormMainParentMDI)
# and dForm == (dFormSDI or dFormChildMDI)
#
# Setting MDI to True on Mac is essential to get a native-feeling Mac app
# where closing the last form doesn't exit the app. Whatever form has the
# focus will determine the menu used - the ParentMDI form is never shown on
# Mac but it's menu will be displayed on the Mac system menu bar.
#
# Setting MDI to True on Windows is still what users expect for most apps.
#
# Setting MDI to True on Linux results in a pageframe setup with each child
# form being a page in the parent pageframe.
MDI = False

# macFontScaling: If you set a font to 10 pt it'll look medium-small on most
# Windows and Linux screens. However, it will look very small on Mac because
# of automatic conversion in OS X. 8pt fonts on Mac are barely even readable.
# Set macFontScaling to True to make your fonts appear the same size on all
# platforms.
macFontScaling = True

# When doing date calculations, displaying calendars, etc., this determines whether
# 'Sunday' or 'Monday' is considered the beginning of the week
firstDayOfWeek = "Sunday"

# Default font size when none other is specified
defaultFontSize = 10

# Default language to use when none is specified
defaultLanguage = "en"

# Override language set in python.locale.getdefaultlocale
overrideLocaleLanguage = False

# Default encoding to use when none is specified
defaultEncoding = "utf-8"

# Default log file for the dabo.debugging.loggit function
loggitFile = "functionCall.log"

# Events should be processed from the latest to earliest binding.
# If you notice that events don't seem to be happening correctly,
# change this to False to see if that improves things. If so, please
# report it the Dabo developers.
reverseEventsOrder = True

# Does the UI layer (dForm) eat exceptions from the biz layer
# such as 'invalid row specified' or bizrule violations and
# automatically display an informational message to the user (True),
# or does the exception go unhandled so that the developer can
# quickly diagnose the issue (False)?
eatBizExceptions = True

# Check for web updates?
checkForWebUpdates = True

# Date and Time formats. None will use the os user's settings, but
# your code can easily override these. Example:
#   dabo.dateFormat = "%d.%m.%Y" -> "31.12.2008".
dateFormat = None
dateTimeFormat = None
timeFormat = None

# Do we load the os user's locale settings automatically?
# Pythonista note: this executes:
#    locale.setlocale(locale.LC_ALL, '')
loadUserLocale = True

# File extensions understood by the getFile functions. The format is a dictionary, with
# the extension as the key, and the descriptive text as the value. To add your own
# custom extensions, create a dict with this same format named 'custom_extensions'
# in your settings_override file, and those will be added to this list.
custom_extensions = {}
file_extensions = {
    "*": "All Files",
    "py": "Python Scripts",
    "txt": "Text Files",
    "log": "Log Files",
    "fsxml": "Dabo FieldSpec Files",
    "cnxml": "Dabo Connection Files",
    "rfxml": "Dabo Report Format Files",
    "cdxml": "Dabo Class Designer Files",
    "mnxml": "Dabo Menu Designer Files",
    "pdf": "PDF Files",
    "js": "Javascript Files",
    "html": "HTML Files",
    "xml": "XML Files",
    "jpg": "JPEG Images",
    "jpeg": "JPEG Images",
    "gif": "GIF Images",
    "tif": "TIFF Images",
    "tiff": "TIFF Images",
    "png": "PNG Images",
    "ico": "Icon Images",
    "bmp": "Bitmap Images",
    "sh": "Shell Scripts",
    "zip": "ZIP Files",
    "tar": "tar Archives",
    "gz": "gzipped Files",
    "tgz": "gzipped tar Archives",
    "mov": "QuickTime Movies",
    "wmv": "Windows Media Videos",
    "mpg": "MPEG Videos",
    "mpeg": "MPEG Videos",
    "mp3": "mp3 Audio Files",
}

# For file-based data backends such as SQLite, do we allow creating a connection to
# a non-existent file, which SQLite will then create?
createDbFiles = False

# URL of the Web Update server
webupdate_urlbase = "http://daboserver.com/webupdate"

# Logging settings
mainLogQualName = "dabo.mainLog"
# Set the main log file to None initially
mainLogFile = None
mainLogConsoleLevel = logging.ERROR
mainLogFileLevel = logging.ERROR
mainLogDateFormat = "%Y-%m-%d %H:%M:%S"
consoleFormat = fileFormat = "%(asctime)s - %(levelname)s - %(message)s"
maxLogFileSize = 5242880  # 5 MB

dbLogLevel = logging.DEBUG
dbLogQualName = "dabo.dbActivityLog"
# Set the db file to None initially
dbLogFile = None
dbLogConsoleLevel = logging.ERROR
dbLogFileLevel = logging.DEBUG
dbLogDateFormat = "%Y-%m-%d %H:%M:%S"
dbConsoleFormat = dbFileFormat = "%(asctime)s - %(levelname)s - %(message)s"
dbMaxLogFileSize = 5242880  # 5 MB

# Report fonts configuration.
reportTTFontFilePath = None
reportTTFontFileMap = {}

# Determines if we import the debugger into the dabo namespace
importDebugger = True

# Do we save the current call stack to dui.lastCallAfterStack in every
# callAfter() call?
saveCallAfterStack = False

# When set to True, data control bound to the dBizobj source is automatically disabled
# if related dataset is empty (RowCount = 0), to prevent user interactions.
autoDisableDataControls = False

dTextBox_NumericBlankToZero = False

# When set to True, dTextBox control bound to the dBizobj source takes its TextLength
# property settings from it.
dTextBox_DeriveTextLengthFromSource = False

# When we copy values from a grid, we need to define the following values for the copied text:
copyValueSeparator = "\t"
copyStringSeparator = '"'
copyLineSeparator = "\n"

# Turn to False for better 'import dabo' performance from inside web apps, for example.
implicitImports = True

# Setting to determine if we call localization.install("dabo") when dabo is imported.
localizeDabo = True

# When field values are float, and DataStructure isn't explicit, do we convert float
# values to Decimal automatically?
convertFloatToDecimal = True

# Root path of the dabo module
root_path = Path(__file__).parent

# Subdirectories that make up a standard Dabo app
standardDirs = ("biz", "cache", "db", "lib", "reports", "resources", "test", "ui")

# Do we do dynamic menu enabling? This was crashing on recent versions of the Class Designer.
dynamicMenuEnabling = False

### Settings - end


# Make sure that the current directory is in the sys.path
sys.path.append(os.getcwd())

# Do not copy/paste anything below this line into settings_override.py.
try:
    from settings_override import *
except ImportError:
    pass

# Encoding to be used throughout the app
_encoding = None


def getEncoding():
    global _encoding
    if _encoding:
        return _encoding
    encoding = locale.getdefaultlocale()[1] or locale.getlocale()[1] or defaultEncoding

    def _getEncodingName():
        if encoding.isdigit():
            # Fix for missing encoding aliases e.g. '874'.
            yield "cp%s" % encoding
        yield encoding
        prefEncoding = locale.getpreferredencoding()
        if not encoding == prefEncoding:
            yield prefEncoding
        if not encoding == defaultEncoding:
            yield defaultEncoding
        raise ValueError("Unknown encoding: %s" % encoding)

    for encoding in _getEncodingName():
        try:
            "".encode(encoding)
        except LookupError:
            pass
        else:
            break
    _encoding = encoding
    return encoding


# Encoding to use with XML
_xml_encoding = None


def getXMLEncoding():
    global _xml_encoding
    if _xml_encoding:
        return _xml_encoding
    encoding = getEncoding()
    if encoding.lower().strip().replace("-", "") == "utf8":
        return "utf-8"
    if "1252" in encoding:
        return "windows-1252"
    _xml_encoding = encoding
    return encoding


# On some platforms getfilesystemencoding() and even getdefaultlocale()
# can return None, so we make sure we always set a reasonable encoding:
fileSystemEncoding = sys.getfilesystemencoding() or locale.getdefaultlocale()[1] or defaultEncoding


@functools.lru_cache
def get_dabo_package():
    """This returns a reference to the main dabo package, which will allow its methods and
    attributes to be available throughout the Dabo codebase.
    """
    try:
        return sys.modules["dabo"]
    except KeyError:
        main_module_name = __package__.split(".")[0]
        return importlib.import_module(main_module_name)


def get_application():
    return get_dabo_package().app_reference


def setup_logging():
    dabo_module = get_dabo_package()
    # These are the various standard log handlers.
    consoleLogHandler = fileLogHandler = None
    dbConsoleLogHandler = dbFileLogHandler = None
    # See if a logging.conf file exists in either the current directory or
    # the base directory for the dabo module. If such a file is found, use
    # it to configure logging. Otherwise, use the values gotten from this file.
    _logConfFileName = "logging.conf"
    _logConfFile = Path.cwd() / _logConfFileName
    if not _logConfFile.exists():
        _logConfFile = root_path / _logConfFileName
    if _logConfFile.exists():
        # If a 'logging.conf' file exists, use it instead of this file's values.
        logging.config.fileConfig(_logConfFile)
        # Populate the module namespace with the appropriate loggers
        log = logging.getLogger(mainLogQualName)
        dbActivityLog = logging.getLogger(dbLogQualName)
        for _handler in log.handlers:
            try:
                _handler.baseFilename
                fileLogHandler = _handler
            except AttributeError:
                consoleLogHandler = _handler
        for _handler in dbActivityLog.handlers:
            try:
                _handler.baseFilename
                dbFileLogHandler = _handler
                break
            except AttributeError:
                dbConsoleLogHandler = _handler
    else:
        # Use the values in this file to configure the logs
        enc = getEncoding()
        consoleLogHandler = logging.StreamHandler()
        consoleLogHandler.setLevel(mainLogConsoleLevel)
        consoleFormatter = logging.Formatter(consoleFormat)
        consoleFormatter.datefmt = mainLogDateFormat
        consoleLogHandler.setFormatter(consoleFormatter)
        dabo_module.logger = logging.getLogger(mainLogQualName)
        dabo_module.logger.setLevel(logging.DEBUG)
        dabo_module.logger.addHandler(consoleLogHandler)
        if mainLogFile is not None:
            fileLogHandler = logging.handlers.RotatingFileHandler(
                filename=mainLogFile, maxBytes=maxLogFileSize, encoding=enc
            )
            fileLogHandler.setLevel(mainLogFileLevel)
            fileFormatter = logging.Formatter(fileFormat)
            fileFormatter.datefmt = mainLogDateFormat
            fileLogHandler.setFormatter(fileFormatter)
            dabo_module.logger.addHandler(fileLogHandler)

        dbConsoleLogHandler = logging.StreamHandler()
        dbConsoleLogHandler.setLevel(dbLogConsoleLevel)
        dbConsoleFormatter = logging.Formatter(dbConsoleFormat)
        dbConsoleFormatter.datefmt = dbLogDateFormat
        dbConsoleLogHandler.setFormatter(dbConsoleFormatter)
        dabo_module.dbActivityLog = logging.getLogger(dbLogQualName)
        dabo_module.dbActivityLog.setLevel(dbLogLevel)
        dabo_module.dbActivityLog.addHandler(dbConsoleLogHandler)
        if dbLogFile is not None:
            dbFileLogHandler = logging.handlers.RotatingFileHandler(
                filename=dbLogFile, maxBytes=maxLogFileSize, encoding=enc
            )
            dbFileLogHandler.setLevel(dbLogFileLevel)
            dbFileFormatter = logging.Formatter(dbFileFormat)
            dbFileFormatter.datefmt = dbLogDateFormat
            dbFileLogHandler.setFormatter(dbFileFormatter)
            dabo_module.dbActivityLog.addHandler(dbFileLogHandler)


# def setMainLogFile(fname=None, level=None):
#     """Create the main file-based logger for the framework, and optionally
#     set the log level. If the passed 'fname' is None, any existing file-based
#     logger will be closed.
#     """
#     dabo_module = get_dabo_package()
#     if fname is None:
#         if dabo_module.fileLogHandler:
#             # Remove the existing handler
#             dabo_module.log.removeHandler(dabo_module.fileLogHandler)
#             dabo_module.fileLogHandler.close()
#             dabo_module.fileLogHandler = None
#     else:
#         if dabo_module.fileLogHandler:
#             # Close the existing handler first
#             dabo_module.log.removeHandler(dabo_module.fileLogHandler)
#             dabo_module.fileLogHandler.close()
#             dabo_module.fileLogHandler = None
#         dabo_module.fileLogHandler = logging.handlers.RotatingFileHandler(
#             filename=fname, maxBytes=maxLogFileSize, encoding=getEncoding()
#         )
#         if level:
#             dabo_module.fileLogHandler.setLevel(level)
#         else:
#             dabo_module.fileLogHandler.setLevel(mainLogFileLevel)
#         dabo_module.fileFormatter = logging.Formatter(fileFormat)
#         dabo_module.fileFormatter.datefmt = mainLogDateFormat
#         dabo_module.fileLogHandler.setFormatter(dabo_module.fileFormatter)
#         dabo_module.logger.addHandler(dabo_module.fileLogHandler)
#
#
# def setDbLogFile(fname=None, level=None):
#     """Create the dbActivity file-based logger for the framework, and optionally
#     set the log level. If the passed 'fname' is None, any existing file-based
#     logger will be closed.
#     """
#     dabo_module = get_dabo_package()
#     if fname is None:
#         if dabo_module.dbFileLogHandler:
#             # Remove the existing handler
#             dabo_module.dbActivityLog.removeHandler(dabo_module.dbFileLogHandler)
#             dabo_module.dbFileLogHandler.close()
#             dabo_module.dbFileLogHandler = None
#     else:
#         if dabo_module.dbFileLogHandler:
#             # Close the existing handler first
#             dabo_module.dbActivityLog.removeHandler(dabo_module.dbFileLogHandler)
#             dabo_module.dbFileLogHandler.close()
#             dabo_module.dbFileLogHandler = None
#         dabo_module.dbFileLogHandler = logging.handlers.RotatingFileHandler(
#             filename=fname, maxBytes=maxLogFileSize, encoding=getEncoding()
#         )
#         if level:
#             dabo_module.dbFileLogHandler.setLevel(level)
#         else:
#             dabo_module.dbFileLogHandler.setLevel(mainLogFileLevel)
#         dabo_module.dbFileFormatter = logging.Formatter(dbFileFormat)
#         dabo_module.dbFileFormatter.datefmt = dbLogDateFormat
#         dabo_module.dbFileLogHandler.setFormatter(dabo_module.dbFileFormatter)
#         dabo_module.dbActivityLog.addHandler(dabo_module.dbFileLogHandler)
#
#
