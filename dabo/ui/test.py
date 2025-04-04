# -*- coding: utf-8 -*-
"""
A simple reusable unit testing framework, used by the base class files when run
as scripts instead of imported as modules.

If you execute, say:
    python dTextBox.py

The dTextBox.py's main section will instantiate class Test and do a simple unit
test of dTextBox.

If you instead run this test.py as a script, a form will be instantiated with
all the dControls.
"""

import importlib
import os
import sys
import traceback
from pathlib import Path

import wx

from .. import settings
from .. import ui
from ..application import dApp

# Log all events except the really frequent ones:
logEvents = ["All", "Idle", "MouseMove"]


class Test(object):
    def __init__(self):
        self.app = dApp()
        self.app.MainFormClass = None
        self.app.setup()

    def runTest(self, classRefs, *args, **kwargs):
        if not isinstance(classRefs, (tuple, list)):
            classRefs = (classRefs,)
        obj_expand = kwargs.pop("obj_expand", True)
        obj_proportion = kwargs.pop("obj_proportion", 1)
        isDialog = False
        if issubclass(classRefs[0], (wx.Frame, wx.Dialog)):
            # Can't display a frame within another frame, so create this
            # class as the main frame
            frame = classRefs[0](None, *args, **kwargs)
            isDialog = issubclass(classRefs[0], wx.Dialog)
        else:
            from . import dForm
            from . import dPanel
            from . import dSizer

            frame = dForm(Name="formTest")
            panel = frame.addObject(dPanel, Name="panelTest")
            panel.Sizer = dSizer("Vertical")
            frame.Sizer.append(panel, 1, "expand")
            frame.testObjects = []
            for class_ in classRefs:
                obj = class_(parent=panel, LogEvents=logEvents, *args, **kwargs)
                panel.Sizer.append(obj, obj_proportion, obj_expand)
                frame.testObjects.append(obj)

            # This will get a good approximation of the required size
            w, h = panel.Sizer.GetMinSize()
            # Some controls don't report sizing correctly, so set a minimum
            w = max(w, 400)
            h = max(h, 300)

            frame.Size = (w + 10, h + 30)
            if len(classRefs) > 1:
                frame.Caption = "Test of multiple objects"
            else:
                frame.Caption = "Test of %s" % obj.BaseClass.__name__

            obj.setFocus()

        if isDialog:
            ret = frame.ShowModal()
            print(ret)
            frame.Destroy()
        else:
            frame.Show()
            frame.Layout()
            self.app.start()

    def testAll(self):
        """Create a dForm and populate it with example dWidgets."""
        from ..ui import dEditBox
        from ..ui import dForm
        from ..ui import dLabel
        from ..ui import dScrollPanel
        from ..ui import dSizer

        frame = dForm(Name="formTestAll")
        frame.Caption = "Test of all the dControls"
        frame.LogEvents = logEvents

        panel = frame.addObject(dScrollPanel, "panelTest")
        panel.SetScrollbars(10, 10, 50, 50)
        labelWidth = 150
        vs = dSizer("vertical")

        # Get all the python modules in this directory into a list:
        dabo_root = settings.root_path
        ui_root = dabo_root / "ui"
        modules = [modname.stem for modname in ui_root.iterdir() if modname.suffix == ".py"]

        for modname in sorted(modules):
            print("==> ", modname)
            # if the module has a test class, instantiate it:
            if modname == "__init__":
                # importing __init__ will pollute the ui namespace and cause
                # isinstance() problems.
                continue
            try:
                mod = importlib.import_module(modname)
            except ImportError as e:
                print("ImportError:", e)
                continue
            objname = "_%s_test" % modname
            if objname in mod.__dict__:
                print("Trying to instantiate %s..." % objname)
                try:
                    obj = mod.__dict__[objname](panel)
                except Exception as e:
                    print("+++++++++++++++++++++++++++++++++++++++")
                    print("+++ Instantiating %s caused:" % objname)
                    print(traceback.print_exception(*sys.exc_info()))
                    print("+++++++++++++++++++++++++++++++++++++++")
                    continue

                if objname == "_dToolBar_test":
                    frame.ToolBar = obj
                    break

                bs = dSizer("horizontal")
                label = dLabel(panel, Alignment="Right", AutoResize=False, Width=labelWidth)

                label.Caption = "%s:" % modname
                bs.append(label)

                if isinstance(obj, dEditBox):
                    layout = "expand"
                else:
                    layout = "normal"

                bs.append(obj, layout)

                if isinstance(obj, dEditBox):
                    vs.append(bs, "expand")
                else:
                    vs.append(bs, "expand")

        panel.Sizer = vs

        fs = frame.Sizer = dSizer("vertical")
        fs.append(panel, "expand", 1)
        fs.layout()
        self.app.MainForm = frame
        self.app.start()


if __name__ == "__main__":
    t = Test()
    t.testAll()
