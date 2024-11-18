import logging
import logging.handlers



def setMainLogFile(fname, level=None):
    """Create the main file-based logger for the framework, and optionally
    set the log level. If the passed 'fname' is None, any existing file-based
    logger will be closed.
    """
    if fname is None:
        if dabo.fileLogHandler:
            # Remove the existing handler
            dabo.log.removeHandler(dabo.fileLogHandler)
            dabo.fileLogHandler.close()
            dabo.fileLogHandler = None
    else:
        if dabo.fileLogHandler:
            # Close the existing handler first
            dabo.log.removeHandler(dabo.fileLogHandler)
            dabo.fileLogHandler.close()
            dabo.fileLogHandler = None
        dabo.fileLogHandler = logging.handlers.RotatingFileHandler(
            filename=fname, maxBytes=maxLogFileSize, encoding=getEncoding()
        )
        if level:
            dabo.fileLogHandler.setLevel(level)
        else:
            dabo.fileLogHandler.setLevel(mainLogFileLevel)
        dabo.fileFormatter = logging.Formatter(fileFormat)
        dabo.fileFormatter.datefmt = mainLogDateFormat
        dabo.fileLogHandler.setFormatter(dabo.fileFormatter)
        dabo.log.addHandler(dabo.fileLogHandler)


def setDbLogFile(fname, level=None):
    """Create the dbActivity file-based logger for the framework, and optionally
    set the log level. If the passed 'fname' is None, any existing file-based
    logger will be closed.
    """
    if fname is None:
        if dabo.dbFileLogHandler:
            # Remove the existing handler
            dabo.dbActivityLog.removeHandler(dabo.dbFileLogHandler)
            dabo.dbFileLogHandler.close()
            dabo.dbFileLogHandler = None
    else:
        if dabo.dbFileLogHandler:
            # Close the existing handler first
            dabo.dbActivityLog.removeHandler(dabo.dbFileLogHandler)
            dabo.dbFileLogHandler.close()
            dabo.dbFileLogHandler = None
        dabo.dbFileLogHandler = logging.handlers.RotatingFileHandler(
            filename=fname, maxBytes=maxLogFileSize, encoding=getEncoding()
        )
        if level:
            dabo.dbFileLogHandler.setLevel(level)
        else:
            dabo.dbFileLogHandler.setLevel(mainLogFileLevel)
        dabo.dbFileFormatter = logging.Formatter(dbFileFormat)
        dabo.dbFileFormatter.datefmt = dbLogDateFormat
        dabo.dbFileLogHandler.setFormatter(dabo.dbFileFormatter)
        dabo.dbActivityLog.addHandler(dabo.dbFileLogHandler)


if localizeDabo:
    # Install localization service for dabo. dApp will install localization service
    # for the user application separately.
    from . import dLocalize

    dLocalize.install("dabo")

if importDebugger:
    from .dBug import logPoint

    try:
        import pudb as pdb
    except ImportError:
        import pdb
    trace = pdb.set_trace

    def debugout(*args):
        from .lib.utils import ustr

        txtargs = [ustr(arg) for arg in args]
        txt = " ".join(txtargs)
        log = logging.getLogger("Debug")
        log.debug(txt)

    # Mangle the namespace so that developers can add lines like:
    #         debugo("Some Message")
    # or
    #         debugout("Another Message", self.Caption)
    # to their code for debugging.
    # (I added 'debugo' as an homage to Whil Hentzen!)
    import builtins

    builtins.debugo = builtins.debugout = debugout

if implicitImports:
    from . import biz
    from . import dColors
    from . import db
    from . import ui
    from . import events

    ui.load_namespace()
    from .dApp import dApp
    from .dPref import dPref
