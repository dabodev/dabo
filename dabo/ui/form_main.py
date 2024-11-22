# -*- coding: utf-8 -*-
import time

import wx

from .. import ui
from . import dFormMixin

# import MDI


class dFormMainBase(dFormMixin):
    """This is the main top-level form for the application."""

    def __init__(self, preClass, parent=None, properties=None, *args, **kwargs):
        dFormMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

    def _beforeClose(self, evt=None):
        # In wxPython 4.x, a 'dead object' is now a logical False.
        forms2close = [frm for frm in self.Application.uiForms if frm and frm is not self]
        # if frm is not self and not isinstance(frm, ui.deadObject)]
        while forms2close:
            frm = forms2close[0]
            # This will allow forms to veto closing (i.e., user doesn't
            # want to save pending changes).
            if frm.close() == False:
                # The form stopped the closing process. The user
                # must deal with this form (save changes, etc.)
                # before the app can exit.
                frm.bringToFront()
                return False
            else:
                forms2close.remove(frm)


class dFormMain(dFormMainBase, wx.Frame):
    def __init__(self, parent=None, properties=None, *args, **kwargs):
        self._baseClass = dFormMain

        if MDI:
            # Hack this into an MDI Parent:
            dFormMain.__bases__ = (dFormMainBase, wx.MDIParentFrame)
            preClass = wx.MDIParentFrame
            self._mdi = True
        else:
            # This is a normal SDI form:
            dFormMain.__bases__ = (dFormMainBase, wx.Frame)
            preClass = wx.Frame
            self._mdi = False
        ## (Note that it is necessary to run the above block each time, because
        ##  we are modifying the dFormMain class definition globally.)

        dFormMainBase.__init__(self, preClass, parent, properties, *args, **kwargs)


ui.dFormMainBase = dFormMainBase
ui.dFormMain = dFormMain


if __name__ == "__main__":
    from ui import test

    test.Test().runTest(dFormMain)
