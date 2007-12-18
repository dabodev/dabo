#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import inspect
import dabo
dabo.ui.loadUI("wx")
from dabo.dLocalize import _
from dabo.ui.dialogs.PreferenceDialog import PreferenceDialog


class PrefEditorPrefDialog(PreferenceDialog):
	def addPages(self):
		dayMins = 24*60
		pm = self.PreferenceManager
		updKey = pm.web_update
		self.preferenceKeys.append(updKey)
		upPage = self.addCategory(_("Web Updates"))

		sz = upPage.Sizer = dabo.ui.dSizer("v")
		hsz = dabo.ui.dSizer("h")
		chkUpdateCheck = dabo.ui.dCheckBox(upPage, OnHit=self.onChkUpdate, 
				Caption=_("Check for Preference Editor updates"), RegID="chkForPrefManUpdates",
				DataSource=updKey, DataField="web_update", 
				ToolTipText="Should we check for updates to the Preference Editor?")
		btnCheckNow = dabo.ui.dButton(upPage, Caption=_("Check now..."),
				OnHit=self.onCheckNow, ToolTipText="Check the Dabo server for updates")
		hsz.append(chkUpdateCheck, valign="middle")
		hsz.appendSpacer(8)
		hsz.append(btnCheckNow, valign="middle")
		sz.append(hsz, halign="center", border=20)
		
		radFrequency = dabo.ui.dRadioList(upPage, Orientation="Vertical", 
				Caption=_("Check every..."), RegID="radWebUpdateFrequency", 
				Choices=[_("Every time an app is run"), _("Once a day"), _("Once a week"), _("Once a month")],
				Keys = [0, dayMins, dayMins*7,dayMins*30],
				ValueMode="Keys", DataSource=updKey, DataField="update_interval",
				ToolTipText=_("How often should we check for updates?"),
				DynamicEnabled = lambda: self.chkForPrefManUpdates.Value)
		sz.append(radFrequency, halign="center")
	
	
	def onChkUpdate(self, evt):
		self.update()
		
		
	def onCheckNow(self, evt):
		ret = self.Application.checkForUpdates(project="prf")


		

def main():
	app = dabo.dApp(BasePrefKey="PrefEditor", MainFormClass="PrefEditor.cdxml",
			PreferenceDialogClass=PrefEditorPrefDialog)
	curdir = os.getcwd()
	# Get the current location's path
	fname = os.path.abspath(inspect.getfile(main))
	pth = os.path.dirname(fname)
	# Switch to that path
	os.chdir(pth)
	app.start()
	
	# Return to the original location
	os.chdir(curdir)



if __name__ == "__main__":
	main()
