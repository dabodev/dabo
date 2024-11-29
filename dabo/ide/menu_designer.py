#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

from .. import ui
from ..dLocalize import _
from ..application import dApp
from .. import events
from ..lib import xmltodict as xtd
from .MenuDesignerForm import MenuDesignerForm


class MenuDesigner(dApp):
    # Behaviors which are normal in the framework may need to
    # be modified when run as the ClassDesigner. This flag will
    # distinguish between the two states.
    isDesigner = True

    def __init__(self, clsFile=""):
        super(MenuDesigner, self).__init__(
            showSplashScreen=False, splashTimeout=10, ignoreScriptDir=True
        )


def main():
    files = sys.argv[1:]
    app = MenuDesigner()
    app.BasePrefKey = "ide.MenuDesigner"
    app.setAppInfo("appName", _("Dabo Menu Designer"))
    app.setAppInfo("appShortName", _("MenuDesigner"))
    #     app._persistentMRUs = {_("File") : onFileMRU}
    app.MainFormClass = None
    app.setup()

    frm = app.MainForm = MenuDesignerForm()
    if files:
        for filename in files:
            frm.openFile(filename)
    frm.show()
    app.start()


if __name__ == "__main__":
    main()
