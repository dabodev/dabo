import functools
import importlib
import logging
import logging.handlers
from pathlib import Path

from . import settings


@functools.lru_cache
def get_dabo_package():
    """This returns a reference to the main dabo package, which will allow its methods and attributes to be available
    throughout the Dabo codebase.
    """
    main_module_name = __package__.split(".")[0]
    return importlib.import_module(main_module_name)


def get_application():
    return get_dabo_package().application


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
#             filename=fname, maxBytes=settings.maxLogFileSize, encoding=settings.getEncoding()
#         )
#         if level:
#             dabo_module.fileLogHandler.setLevel(level)
#         else:
#             dabo_module.fileLogHandler.setLevel(settings.mainLogFileLevel)
#         dabo_module.fileFormatter = logging.Formatter(settings.fileFormat)
#         dabo_module.fileFormatter.datefmt = settings.mainLogDateFormat
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
#             filename=fname, maxBytes=settings.maxLogFileSize, encoding=settings.getEncoding()
#         )
#         if level:
#             dabo_module.dbFileLogHandler.setLevel(level)
#         else:
#             dabo_module.dbFileLogHandler.setLevel(settings.mainLogFileLevel)
#         dabo_module.dbFileFormatter = logging.Formatter(settings.dbFileFormat)
#         dabo_module.dbFileFormatter.datefmt = settings.dbLogDateFormat
#         dabo_module.dbFileLogHandler.setFormatter(dabo_module.dbFileFormatter)
#         dabo_module.dbActivityLog.addHandler(dabo_module.dbFileLogHandler)
#
#
def setup_logging():
    dabo_module = get_dabo_package()
    # These are the various standard log handlers.
    consoleLogHandler = fileLogHandler = None
    dbConsoleLogHandler = dbFileLogHandler = None
    # See if a logging.conf file exists in either the current directory or
    # the base directory for the dabo module. If such a file is found, use
    # it to configure logging. Otherwise, use the values gotten from
    # dabo.settings.
    _logConfFileName = "logging.conf"
    _logConfFile = Path.cwd() / _logConfFileName
    if not _logConfFile.exists():
        _logConfFile = settings.root_path / _logConfFileName
    if _logConfFile.exists():
        # If a 'logging.conf' file exists, use it instead of dabo.settings.
        logging.config.fileConfig(_logConfFile)
        # Populate the module namespace with the appropriate loggers
        log = logging.getLogger(settings.mainLogQualName)
        dbActivityLog = logging.getLogger(settings.dbLogQualName)
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
        # Use dabo.settings values to configure the logs
        enc = settings.getEncoding()
        consoleLogHandler = logging.StreamHandler()
        consoleLogHandler.setLevel(settings.mainLogConsoleLevel)
        consoleFormatter = logging.Formatter(settings.consoleFormat)
        consoleFormatter.datefmt = settings.mainLogDateFormat
        consoleLogHandler.setFormatter(consoleFormatter)
        dabo_module.logger = logging.getLogger(settings.mainLogQualName)
        dabo_module.logger.setLevel(logging.DEBUG)
        dabo_module.logger.addHandler(consoleLogHandler)
        if settings.mainLogFile is not None:
            fileLogHandler = logging.handlers.RotatingFileHandler(
                filename=settings.mainLogFile, maxBytes=settings.maxLogFileSize, encoding=enc
            )
            fileLogHandler.setLevel(settings.mainLogFileLevel)
            fileFormatter = logging.Formatter(settings.fileFormat)
            fileFormatter.datefmt = settings.mainLogDateFormat
            fileLogHandler.setFormatter(fileFormatter)
            dabo_module.logger.addHandler(fileLogHandler)

        dbConsoleLogHandler = logging.StreamHandler()
        dbConsoleLogHandler.setLevel(settings.dbLogConsoleLevel)
        dbConsoleFormatter = logging.Formatter(settings.dbConsoleFormat)
        dbConsoleFormatter.datefmt = settings.dbLogDateFormat
        dbConsoleLogHandler.setFormatter(dbConsoleFormatter)
        dabo_module.dbActivityLog = logging.getLogger(settings.dbLogQualName)
        dabo_module.dbActivityLog.setLevel(settings.dbLogLevel)
        dabo_module.dbActivityLog.addHandler(dbConsoleLogHandler)
        if settings.dbLogFile is not None:
            dbFileLogHandler = logging.handlers.RotatingFileHandler(
                filename=settings.dbLogFile, maxBytes=settings.maxLogFileSize, encoding=enc
            )
            dbFileLogHandler.setLevel(settings.dbLogFileLevel)
            dbFileFormatter = logging.Formatter(settings.dbFileFormat)
            dbFileFormatter.datefmt = settings.dbLogDateFormat
            dbFileLogHandler.setFormatter(dbFileFormatter)
            dabo_module.dbActivityLog.addHandler(dbFileLogHandler)
