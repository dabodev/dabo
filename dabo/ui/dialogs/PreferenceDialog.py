# -*- coding: utf-8 -*-
import dabo
from dabo.dLocalize import _

dayMins= 24*60



class PreferenceDialog(dabo.ui.dOkCancelDialog):
	def addControls(self):
		"""Add the base PageList, and then delete this method from the 
		namespace. Users will customize with addCategory() and then 
		adding controls to the category page.
		"""
		self.Caption = _("Preferences")
		self.pglCategory = dabo.ui.dPageList(self, TabPosition="Left", Size=(500, 400))
		self.Sizer.append1x(self.pglCategory)
		# Set up a list of functions to call when the user clicks 'OK' to accept changes
		self.callOnAccept = []
		# Use this to 'delete' addControls() so that users don't try to use this method.
		self.addControls = None
	
	
	def _onAccept(self):
		"""This is called by the app when the user clicks the OK button. Every method in
		the callOnAccept list is called, followed by a call to the user-configurable 
		onAccept() method.
		"""
		for fnc in self.callOnAccept:
			fnc()
		# Call the user-configurable method
		self.onAccept()
	
	
	def onAccept(self):
		"""Override this for subclasses where you need separate OK processing."""
		pass
		

	def addCategory(self, category, pos=None):
		"""Adds a page to the main PageList control, sets the caption to the
		passed string, and returns a reference to the page. If the optional 'pos'
		parameter is passed, the page is inserted in that position; otherwise, it
		is appended after any existing pages.
		"""
		if pos is None:
			pos = self.pglCategory.PageCount
		return self.pglCategory.insertPage(pos, caption=category)
	
	
	def _stub(self):
		"""Called when no other code exists to fill the dialog."""
		wuPage = self.pgWebUpdate = self.addCategory("Web Update")
		wuPage.BackColor = "yellow"
		sz = wuPage.Sizer = dabo.ui.dSizer("v")
		hsz = dabo.ui.dSizer("h")
		chkUpdateCheck = dabo.ui.dCheckBox(wuPage, Caption=_("Check for framework updates"),
				OnHit=self.onChkUpdate, RegID="chkForWebUpdates",
				ToolTipText="Does the framework check for updates?")
		btnCheckNow = dabo.ui.dButton(wuPage, Caption=_("Check now..."),
				OnHit=self.onCheckNow, ToolTipText="Check the Dabo server for updates")
		hsz.append(chkUpdateCheck, valign="middle")
		hsz.appendSpacer(8)
		hsz.append(btnCheckNow, valign="middle")
		sz.append(hsz, halign="center", border=20)
		
		radFrequency = dabo.ui.dRadioList(wuPage, Orientation="Vertical", ValueMode="Keys", 
				Choices=[_("Every time an app is run"), _("Once a day"), _("Once a week"), _("Once a month")],
				Keys = [0, dayMins, dayMins*7,dayMins*30],
				Caption=_("Check every..."), RegID="radWebUpdateFrequency", 
				ToolTipText=_("How often does the framework check for updates?"),
				DynamicEnabled = self.wantsUpdates)
		sz.append(radFrequency, halign="center")
		self.chkForWebUpdates.Value, self.radWebUpdateFrequency.Value = self.Application.getWebUpdateInfo()
		dabo.ui.callAfter(self.update)
		self.layout()

		# Set the callback to process the user's choices when they click OK.
		self.callOnAccept.append(self._saveWebUpdateSettings)
	
	
	def _saveWebUpdateSettings(self):
		shouldUpdate = self.chkForWebUpdates.Value
		freq = self.radWebUpdateFrequency.Value
		self.Application._setWebUpdate(shouldUpdate, interval=freq)


	def wantsUpdates(self):
		return self.chkForWebUpdates.Value


	def getFrequency(self):
		pos = self.radWebUpdateFrequency.PositionValue
		return {0: 0, 1: dayMins, 2: dayMins*7, 3: dayMins*30}[pos]


	def onChkUpdate(self, evt):
		self.update()
		
		
	def onCheckNow(self, evt):
		ret = self.Application.checkForUpdates()
		if ret:
			dabo.ui.info(_("No updates are available now."), title=_("Web Updates"))
