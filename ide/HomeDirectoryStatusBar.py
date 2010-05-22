#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dabo
from dabo.dLocalize import _
dabo.ui.loadUI("wx")


class HomeDirectoryStatusBar(dabo.ui.dStatusBar):
	"""This class is designed to be used in the visual tools to replace the regular StatusBar
	in the main form. The idea is that when using the tools, it is important to know the
	HomeDirectory that Dabo is using, as pathing is calculated relative to that for all
	values that contain paths. It also provides a convenient way to change the HomeDirectory
	by clicking on the hyperlink.
	"""
	def afterInit(self):
		# The target we are setting the HomeDirectory is usually the Application, but can also
		# be the form itself. If the form sets the target, use that. Otherwise, default
		# to the Application.
		try:
			self._target = self.Form.getHomeDirectoryTarget()
		except AttributeError:
			self._target = self.Application
		link = self.linkChangeHD = dabo.ui.dHyperLink(self, Caption=_("Home Directory: "),
				ShowInBrowser=False, OnHit=self._changeHD)
		link.VisitedColor = link.LinkColor = "blue"
		txt = self.txtHD = dabo.ui.dTextBox(self, Enabled=False, DataSource=self._target,
				DataField="HomeDirectory")
		sz = self.Sizer = dabo.ui.dSizer("H")
		sz.appendSpacer(4)
		sz.append(link)
		sz.append(txt, 1)
		dabo.ui.callAfter(self.update)
		dabo.ui.callAfter(self.layout)
		# Necessary so that this works in the Class Designer
		txt._designerMode = False


	def _changeHD(self, evt):
		dirname = dabo.ui.getDirectory(_("Select Home Directory"), self._target.HomeDirectory)
		if dirname:
			self._target.HomeDirectory = dirname
			self.update()


	def SetStatusText(self, val, fld=0):
		# Don't allow status text
		pass


if __name__ == "__main__":
	class HDForm(dabo.ui.dForm):
		def beforeInit(self):
			self.StatusBarClass = HomeDirectoryStatusBar


	app = dabo.dApp(MainFormClass=HDForm)
	app.start()
