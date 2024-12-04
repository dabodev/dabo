# dIconsdIcons -*- coding: utf-8 -*-
"""
3-Tier Desktop Database Business Application Framework

http://dabodev.com
"""

import asyncio
import builtins
import importlib
import locale
import os
import sys
from functools import partial
from pathlib import Path

from . import settings
from . import application
from . import settings
from . import version


# Reference to the running application object
app_reference = None


# Current version
def get_version():
    return version.get_version()


# Method to create a standard Dabo directory structure layout
def makeDaboDirectories(homedir=None):
    """If homedir is passed, the directories will be created off of that
    directory. Otherwise, it is assumed that they should be created
    in the current directory location.
    """
    dabo_loc = __file__
    curr_loc = None
    if homedir:
        curr_loc = Path.cwd()
        os.chdir(homedir)
    for d in settings.standardDirs:
        dirpath = Path(d)
        dirpath.mkdir(parents=True, exist_ok=True)
    if curr_loc:
        os.chdir(curr_loc)


# Ensure that the minimal structure is present
makeDaboDirectories()


def _load_base_modules():
    from . import dConstants
    from . import events
    from . import dObject
    from . import dException


def _load_remaining_modules():
    from . import db
    from . import dPref
    from . import ui

    ui.load_namespace()
    from . import settings
    from . import biz
    from . import dColors
    from . import events


# if settings.implicitImports:
#     asyncio.ensure_future(_load_modules())

# Load the base modules first
_load_base_modules()
# Now load the rest
_load_remaining_modules()

# Logging configuration
logger = None
dbActivityLog = None
fileFormatter = None
fileLogHandler = None
dbFileLogHandler = None
dbFileFormatter = None
settings.setup_logging()
debug = logger.debug
info = logger.info
error = logger.error


if settings.localizeDabo:
    # Install localization service for dabo. dApp will install localization service
    # for the user application separately.
    from . import dLocalize

    dLocalize.install("dabo")

if settings.importDebugger:
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
    builtins.debugo = builtins.debugout = debugout


def quickStart(homedir=None):
    """This creates a bare-bones application in either the specified
    directory, or the current one if none is specified.
    """
    currLoc = os.getcwd()
    if homedir is None:
        homedir = input("Enter the name for your application: ")
    if not homedir:
        return

    if not os.path.exists(homedir):
        os.makedirs(homedir)
    os.chdir(homedir)
    makeDaboDirectories()
    open("main.py", "w").write(
        """#!/usr/bin/env python
# -*- coding: utf-8 -*-
from . import ui
from application import dApp

app = dApp()

# IMPORTANT! Change app.MainFormClass value to the name
# of the form class that you want to run when your
# application starts up.
app.MainFormClass = ui.dFormMain

app.start()
"""
    )

    template = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
######
# In order for Dabo to 'see' classes in your %(dd)s directory, add an
# import statement here for each class. E.g., if you have a file named
# 'MyClasses.py' in this directory, and it defines two classes named 'FirstClass'
# and 'SecondClass', add these lines:
#
# from MyClasses import FirstClass
# from MyClasses import SecondClass
#
# Now you can refer to these classes as: self.Application.%(dd)s.FirstClass and
# self.Application.%(dd)s.SecondClass
######

"""
    for dd in _standardDirs:
        fname = "%s/__init__.py" % dd
        txt = template % locals()
        open(fname, "w").write(txt)
    os.chmod("main.py", 744)
    os.chdir(currLoc)
    print("Application '%s' has been created for you" % homedir)
