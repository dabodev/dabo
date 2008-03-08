#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import dabo
from dabo.dLocalize import _
import dabo.dEvents as dEvents
import dabo.lib.xmltodict as xtd
from MenuDesignerForm import MenuDesignerForm

if __name__ == "__main__":
	dabo.ui.loadUI("wx")


if __name__ == "__main__":
	app = dabo.dApp()		
	app.MainFormClass = MenuDesignerForm
	app.start()

