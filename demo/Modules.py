# -*- coding: utf-8 -*-
"""These classes are taken from the wxPython demo, and
modified to be consistent with Dabo style guidelines. Otherwise,
they are essentially the work of Robin Dunn. Here is the
header from the Main.py file from which they were lifted:

#----------------------------------------------------------------------------
# Name:            Main.py
# Purpose:        Testing lots of stuff, controls, window types, etc.
#
# Author:        Robin Dunn
#
# Created:        A long time ago, in a galaxy far, far away...
# RCS-ID:        $Id: Main.py,v 1.168.2.8 2006/03/15 23:57:39 RD Exp $
# Copyright:    (c) 1999 by Total Control Software
# Licence:        wxWindows license
#----------------------------------------------------------------------------
"""

import os
import sys
import traceback
import types
import dabo.ui
import dabo.lib.utils as utils
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.lib.utils import ustr
from dabo.ui import dPanel


class ModuleDictWrapper:
    """Emulates a module with a dynamically compiled __dict__"""

    def __init__(self, dict):
        self.dict = dict

    def __getattr__(self, name):
        if name in self.dict:
            return self.dict[name]
        else:
            raise AttributeError


class DemoModules:
    """Dynamically manages the original/modified versions of a demo
    module.
    """

    modOrig = 0
    modMod = 1
    origDir = os.path.join(dabo.dAppRef.HomeDirectory, "samples")
    try:
        getUserAppDataDirectory = utils.getUserAppDataDirectory
    except AttributeError:
        # Used to be named differently. Keep this for backward-compatibility for a while.
        getUserAppDataDirectory = utils.getUserDaboDirectory
    modDir = os.path.join(getUserAppDataDirectory(), "DaboDemo", "modified")
    if not os.path.exists(modDir):
        os.makedirs(modDir)

    def __init__(self, name):
        self.modActive = -1
        # Index used in self.modules for orig and modified versions
        self.name = name
        #               (dict , source ,     filename , description      , error information )
        #               (  0     ,     1      ,        2      ,         3          ,             4          )
        self.modules = [
            [None, "", "", "<original>", None],
            [None, "", "", "<modified>", None],
        ]

        fname = "%s/%s.py" % (self.origDir, name)
        # load original module
        self.loadFromFile(fname, self.modOrig)
        self.setActive(self.modOrig)

        # load modified module (if one exists)
        modName = "%s/%s.py" % (self.modDir, name)
        if os.path.exists(modName):
            self.loadFromFile(modName, self.modMod)

    def loadFromFile(self, filename, modID):
        self.modules[modID][2] = filename
        self.loadFromSource(open(filename, "rt").read(), modID)

    def loadFromSource(self, source, modID):
        self.modules[modID][1] = source
        self.loadDict(modID)

    def loadDict(self, modID):
        if self.name != __name__:
            source = self.modules[modID][1]
            if source.strip().startswith("# -*- coding:"):
                srclines = [
                    ln for ln in source.strip().splitlines() if not ln.startswith("# -*- coding:")
                ]
                source = "\n".join(srclines)
            # description = self.modules[modID][3]
            description = self.modules[modID][2]
            try:
                self.modules[modID][0] = {}
                code = compile(source, description, "exec")
                exec(code, self.modules[modID][0])
            except Exception:
                self.modules[modID][4] = DemoError(sys.exc_info())
                self.modules[modID][0] = None
            else:
                self.modules[modID][4] = None

    def setActive(self, modID):
        self.modActive = modID

    def getActive(self):
        dict = self.modules[self.modActive][0]
        if dict is None:
            return None
        else:
            return ModuleDictWrapper(dict)

    def getActiveID(self):
        return self.modActive

    def getSource(self, modID=None):
        if modID is None:
            modID = self.modActive
        return self.modules[modID][1]

    def getFilename(self, modID=None):
        if modID is None:
            modID = self.modActive
        return self.modules[modID][2]

    def getErrorInfo(self, modID=None):
        if modID is None:
            modID = self.modActive
        return self.modules[modID][4]

    def exists(self, modID):
        return self.modules[modID][1] != ""

    def hasModified(self):
        return self.modules[self.modMod][1] != ""

    def saveMod(self, code):
        if os.linesep != "\n":
            code = code.replace(os.linesep, "\n")
        fname = self.modules[self.modMod][2]
        if not fname:
            base = os.path.split(self.modules[self.modOrig][2])[-1]
            fname = self.modules[self.modMod][2] = os.path.join(self.modDir, base)
        self.modules[self.modMod][1] = code
        self.updateFile(self.modMod)
        self.loadDict(self.modMod)

    def getOrigDir(cls):
        return cls.origDir

    getOrigDir = classmethod(getOrigDir)

    def getModDir(cls):
        return cls.modDir

    getModDir = classmethod(getModDir)

    def deleteModified(self):
        fname = self.modules[self.modMod][2]
        if not fname:
            # nothing to delete!
            return
        self.modules[self.modMod][1] = ""
        os.remove(fname)

    def updateFile(self, modID=None):
        """Updates the file from which a module was loaded
        with (possibly updated) source
        """
        if modID is None:
            modID = self.modActive
        source = self.modules[modID][1]
        filename = self.modules[modID][2]
        try:
            file = open(filename, "wt")
            file.write(source)
        finally:
            file.close()

    def delete(self, modID):
        if self.modActive == modID:
            self.setActive(0)
        self.modules[modID][0] = None
        self.modules[modID][1] = ""
        self.modules[modID][2] = ""


# ---------------------------------------------------------------------------


class DemoError:
    """Wraps and stores information about the current exception"""

    def __init__(self, exc_info):
        import copy

        excType, excValue = exc_info[:2]
        # traceback list entries: (filename, line number, function name, text)
        self.traceback = traceback.extract_tb(exc_info[2])

        # --Based on traceback.py::format_exception_only()--
        if type(excType) == type:
            self.exception_type = excType.__name__
        else:
            self.exception_type = excType

        # If it's a syntax error, extra information needs
        # to be added to the traceback
        if excType is SyntaxError:
            try:
                msg, (filename, lineno, self.offset, line) = excValue
            except Exception:
                pass
            else:
                if not filename:
                    filename = "<string>"
                if line is not None:
                    line = line.strip()
                self.traceback.append((filename, lineno, "", line))
                excValue = msg
        try:
            self.exception_details = ustr(excValue)
        except Exception:
            self.exception_details = "<unprintable %s object>" & type(excValue).__name__

        del exc_info

    def __str__(self):
        ret = (
            "Type %s \n \
        Traceback: %s \n \
        Details     : %s"
            % (ustr(self.exception_type), ustr(self.traceback), self.exception_details)
        )
        return ret


# ---------------------------------------------------------------------------


class DemoErrorPanel(dPanel):
    """Panel put into the demo tab when the demo fails to run due  to errors"""

    def setErrorInfo(self, codePanel, demoError):
        self.codePanel = codePanel
        sz = self.Sizer = dabo.ui.dSizer("v")
        lbl = dabo.ui.dLabel(
            self,
            Caption=_("An error has occurred while trying to run the demo"),
            ForeColor="red",
        )
        lbl.FontSize += 2
        sz.append(lbl, halign="center", border=10)

        bs = dabo.ui.dBorderSizer(self, "v", Caption=_("Exception Info"))
        gs = dabo.ui.dGridSizer(MaxCols=2, HGap=5, VGap=2)
        gs.append(dabo.ui.dLabel(self, Caption=_("Type:"), FontBold=True), halign="right")
        gs.append(dabo.ui.dLabel(self, Caption=demoError.exception_type), halign="left")
        gs.append(dabo.ui.dLabel(self, Caption=_("Details:"), FontBold=True), halign="right")
        gs.append(dabo.ui.dLabel(self, Caption=demoError.exception_details), halign="left")
        bs.append(gs, border=8)
        sz.append(bs, halign="center", border=5)

        lst = self.tbList = dabo.ui.dListControl(self, BorderStyle="sunken", MultipleSelect=False)
        lst.bindEvent(dEvents.MouseLeftDoubleClick, self.onListDoubleClick)
        lst.addColumn(_("Filename"))
        lst.addColumn(_("Line"))
        lst.addColumn(_("Function"))
        lst.addColumn(_("Code"))
        self.insertTraceback(lst, demoError.traceback)
        lst.autoSizeColumns((0, 1, 2))

        sz.appendSpacer(10)
        sz.append(dabo.ui.dLabel(self, Caption=_("Traceback")))
        sz.appendSpacer(5)
        sz.append1x(lst, border=5)
        lbl = dabo.ui.dLabel(
            self,
            Caption=_("""Entries from the demo module are shown in blue.
Double-click on them to go to the offending line."""),
        )
        sz.append(lbl, halign="center")
        sz.appendSpacer(5)
        self.layout()

    def insertTraceback(self, lst, traceback):
        # Add the traceback data
        for tbNum in range(len(traceback)):
            data = traceback[tbNum]
            lst.append((os.path.basename(data[0]), ustr(data[1]), ustr(data[2]), ustr(data[3])))

            # Check whether this entry is from the demo module
            pth = os.path.split(data[0])[0]
            codeDirs = (DemoModules.getOrigDir(), DemoModules.getModDir())
            if pth in codeDirs:
                lst.setItemData(tbNum, int(data[1]))  # Store line number for easy access
                # Give it a blue colour
                lst.setItemForeColor(tbNum, "blue")
            else:
                lst.setItemData(tbNum, -1)  # Editor can't jump into this one's code

    def onListDoubleClick(self, evt):
        # If double-clicking on a demo's entry, jump to the line number
        num = self.tbList.getItemData(self.tbList.PositionValue)
        dabo.ui.callAfter(self.Form.showCode, num)
