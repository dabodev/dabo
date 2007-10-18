#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob
from distutils.core import setup
import py2exe
import dabo.icons
from App import App

# Find the location of the dabo icons:
iconDir = os.path.split(dabo.icons.__file__)[0]

# The applications App object contains all the meta info:
app = App(MainFormClass=None)
app.setup()


_appName = app.getAppInfo("appName")
_appVersion = app.getAppInfo("appVersion")
_appDescription = app.getAppInfo("appDescription")
_copyright = app.getAppInfo("copyright")
_authorName = app.getAppInfo("authorName") 
_authorEmail = app.getAppInfo("authorEmail")
_authorURL = app.getAppInfo("authorURL")
_authorPhone = app.getAppInfo("authorPhone")


_appComments = ("This is custom software by %s.\r\n"
		"\r\n"
		"%s\r\n" 
		"%s\r\n" 
		"%s\r\n") % (_authorName, _authorEmail, _authorURL, _authorPhone)

# Set your app icon here:
_appIcon = None
#_appIcon = "./resources/stock_addressbook.ico"

_script = "webtest.py"


class Target:
	def __init__(self, **kw):
		self.__dict__.update(kw)
		# for the versioninfo resources
		self.version = _appVersion
		self.company_name = _authorName
		self.copyright = _copyright
		self.name = _appName
		self.description = _appDescription
		self.comments = _appComments

		self.script=_script
		self.other_resources=[]
		if _appIcon is not None:
			self.icon_resources=[(1, _appIcon)]


setup(name=_appName,
      version=_appVersion,
      description=_appDescription,
      author=_authorName,
      author_email=_authorEmail,
      url=_authorURL,
      options={"py2exe": {"packages": ["wx.gizmos"],
                          "optimize": 2,
                          "excludes": ["Tkconstants","Tkinter","tcl", 
                                       "_imagingtk", "PIL._imagingtk",
                                       "ImageTk", "PIL.ImageTk", "FixTk"]}},
      packages=["ui", "biz", "db"],
      zipfile=None,
      windows=[Target()],
      data_files=[("db", ["db/default.cnxml"]),
                  ("ui", ["ui/fieldSpecs.fsxml", "ui/relationSpecs.rsxml"]),
                  ("resources", glob.glob(os.path.join(iconDir, "*.png"))),
                  ("resources", glob.glob(os.path.join(iconDir, "*.ico"))),
                  ("resources", glob.glob("resources/*")),
                  ("reports", glob.glob("reports/*"))]
     )

