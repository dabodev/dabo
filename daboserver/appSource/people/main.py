#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")

app = dabo.dApp(SourceURL="http://daboserver.com:7777")

# IMPORTANT! Change app.MainFormClass value to the name
# of the form class that you want to run when your
# application starts up.
app.MainFormClass = "people.cdxml"

app.start()
