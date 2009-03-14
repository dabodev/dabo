#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")
from dabo.lib import utils

if __name__ == "__main__":
	app = dabo.dApp()
	app.BasePrefKey = "dabo.springboard"
	app.MainFormClass = "springboard.cdxml"
	app.PreferenceManager.local_storage_dir = utils.getUserAppDataDirectory()
	
	app.start()
