#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import dabo
from dabo.dLocalize import _
import dabo.dEvents as dEvents
import dabo.lib.xmltodict as xtd
dabo.ui.loadUI("wx")
from MenuDesignerForm import MenuDesignerForm

def main():
	files = sys.argv[1:]
	app = dabo.dApp()
	app.BasePrefKey = "ide.MenuDesigner"
	app.setAppInfo("appName", _("Dabo Menu Designer"))
	app.setAppInfo("appShortName", _("MenuDesigner"))
# 	app._persistentMRUs = {_("File") : onFileMRU}
	app.MainFormClass = None
	app.setup()

	frm = app.MainForm = MenuDesignerForm()
	for file in files:
		frm.openFile(file)
	frm.show()
	app.start()
	


if __name__ == "__main__":
	main()

