#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dabo
import dabo.db
import dabo.biz
import dabo.lib
import dabo.ui
dabo.ui.loadUI("wx")
import dabo.lib.autosuper
import dabo.lib.datanav
import dabo.lib.datanav2
import dabo.ui.dialogs



if __name__ == "__main__":
	app = dabo.dApp()
	app.BasePrefKey = "dabo.springboard"
	app.MainFormClass = "springboard.cdxml"
	app.PreferenceManager.local_storage_dir = dabo.lib.utils.getUserAppDataDirectory()
	
	app.start()
