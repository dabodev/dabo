# -*- coding: utf-8 -*-
"""
3-Tier Desktop Database Business Application Framework

http://dabodev.com
"""

import importlib
import locale
import os
import sys

from .settings import *


# dApp will change the following values upon its __init__:
dAppRef = None


# Method to create a standard Dabo directory structure layout
def makeDaboDirectories(homedir=None):
    """If homedir is passed, the directories will be created off of that
    directory. Otherwise, it is assumed that they should be created
    in the current directory location.
    """
    currLoc = os.getcwd()
    if homedir is not None:
        os.chdir(homedir)
    # 'standardDirs' is defined in settings.py
    for d in standardDirs:
        if not os.path.exists(d):
            os.mkdir(d)
    os.chdir(currLoc)


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
from dabo import ui as dui
from dabo.dApp import dApp

app = dApp()

# IMPORTANT! Change app.MainFormClass value to the name
# of the form class that you want to run when your
# application starts up.
app.MainFormClass = dui.dFormMain

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
