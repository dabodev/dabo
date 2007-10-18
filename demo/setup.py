#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")
import dabo.icons
import glob
import os
from distutils.core import setup
import py2exe

# Find the location of the dabo icons:
iconDir = os.path.split(dabo.icons.__file__)[0]

setup(name="DaboDemo",
		description="Dabo UI demo program",
		author="Ed Leafe",
		options={"py2exe": {"packages": ["wx.gizmos", "wx.lib.masked",
					"wx.lib.calendar"],
				"optimize": 2,
				"excludes": ["kinterbasdb", "MySQLdb", "psycopg"],
				"includes": ["Modules"]}
				},
		console = ["DaboDemo.py"],
		data_files=[("media", glob.glob("media/*")),
				("icons", glob.glob(os.path.join(iconDir, "*.png"))),
				("icons", glob.glob(os.path.join(iconDir, "*.ico"))),
				(".", ["DaboDemo.cdxml", "DaboDemo-code.py"]),
				("samples", glob.glob("samples/*py"))]
)

# To build, run:
#
# python setup.py py2exe --bundle 1
