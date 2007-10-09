# -*- coding: utf-8 -*-
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
from dabo.dLocalize import _

dayMins= 24*60



class PreferenceDialog(dabo.ui.dOkCancelDialog):
	def _afterInit(self):
		self._includeDefaultPages = False
		self.Size = (700, 600)
		self.AutoSize = False
		self.Caption = _("Preferences")
		# Set up a list of functions to call when the user clicks 'OK' to accept changes,
		# and one for functions to call when the user cancels.
		self.callOnAccept = []
		self.callOnCancel = []
		# Create a list of preference key objects that will be have their AutoPersist turned
		# off when the dialog is shown, and either canceled or persisted, depending
		# on the user's action.
		self.preferenceKeys = []
		super(PreferenceDialog, self)._afterInit()
	

	def addControls(self):
		"""Add the base PageList, and then delete this method from the 
		namespace. Users will customize with addCategory() and then 
		adding controls to the category page.
		"""
		self._addPages()
# 		dabo.ui.callAfter(self.pglCategory.fitToSizer)
		# Use this to 'delete' addControls() so that users don't try to use this method.
		self.addControls = None
	
	
	def _addPages(self):
		self.pglCategory = dabo.ui.dPageList(self, TabPosition="Left",
				ListSpacing=20)
		self.addPages()
		if self.pglCategory.PageCount == 0 or self.IncludeDefaultPages:
			self._addDefaultPages()
		self.Sizer.append1x(self.pglCategory)
		self.layout()
	
	
	def addPages(self): pass
	
	
	def _onAcceptPref(self):
		"""This is called by the app when the user clicks the OK button. Every method in
		the callOnAccept list is called, followed by a call to the user-configurable 
		onAccept() method.
		"""
		for fnc in self.callOnAccept:
			fnc()
		# Call the user-configurable method
		self.onAcceptPref()
	
	
	def onAcceptPref(self):
		"""Override this for subclasses where you need separate OK processing."""
		pass
		

	def _onCancelPref(self):
		"""This is called by the app when the user clicks the Cancel button. Every method 
		in the callOnCancel list is called, followed by a call to the user-configurable 
		onCancel() method.
		"""
		for fnc in self.callOnCancel:
			fnc()
		# Call the user-configurable method
		self.onCancelPref()
	
	
	def onCancelPref(self):
		"""Override this for subclasses where you need separate Cancel processing."""
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
	
	
	def _addDefaultPages(self):
		"""Called when no other code exists to fill the dialog, or when
		the class's IncludeDefaultPages is True.
		"""
		wuPage = self.pgWebUpdate = self.addCategory(_("Web Update"))
		# Set the framework-level pref manager
		fp = self.Application._frameworkPrefs
		self.preferenceKeys.append(fp)
		sz = wuPage.Sizer = dabo.ui.dSizer("v")
		hsz = dabo.ui.dSizer("h")
		chkUpdateCheck = dabo.ui.dCheckBox(wuPage, OnHit=self.onChkUpdate, 
				Caption=_("Check for framework updates"), RegID="chkForWebUpdates",
				DataSource=fp, DataField="web_update", 
				ToolTipText="Does the framework check for updates?")
		btnCheckNow = dabo.ui.dButton(wuPage, Caption=_("Check now..."),
				OnHit=self.onCheckNow, ToolTipText="Check the Dabo server for updates")
		hsz.append(chkUpdateCheck, valign="middle")
		hsz.appendSpacer(8)
		hsz.append(btnCheckNow, valign="middle")
		sz.append(hsz, halign="center", border=20)
		
		radFrequency = dabo.ui.dRadioList(wuPage, Orientation="Vertical", 
				Caption=_("Check every..."), RegID="radWebUpdateFrequency", 
				Choices=[_("Every time an app is run"), _("Once a day"), _("Once a week"), _("Once a month")],
				Keys = [0, dayMins, dayMins*7,dayMins*30],
				ValueMode="Keys", DataSource=fp, DataField="update_interval",
				ToolTipText=_("How often does the framework check for updates?"),
				DynamicEnabled = lambda: self.chkForWebUpdates.Value)
		sz.append(radFrequency, halign="center")
		wui = self.Application.getWebUpdateInfo()
		self.chkForWebUpdates.Value, self.radWebUpdateFrequency.Value = wui
		dabo.ui.callAfter(self.update)
		self.layout()
	
	
	def onChkUpdate(self, evt):
		self.update()
		
		
	def onCheckNow(self, evt):
		ret = self.Application.checkForUpdates()
		if ret:
			dabo.ui.info(_("No updates are available now."), title=_("Web Updates"))
	
	def _getIncludeDefaultPages(self):
		return self._includeDefaultPages

	def _setIncludeDefaultPages(self, val):
		if self._constructed():
			self._includeDefaultPages = val
		else:
			self._properties["IncludeDefaultPages"] = val


	IncludeDefaultPages = property(_getIncludeDefaultPages, _setIncludeDefaultPages, None,
			_("""When True, the _addDefaultPages() method is called to add the common 
			Dabo settings. Default=False  (bool)"""))


if __name__ == "__main__":
	app = dabo.dApp(MainFormClass=None)
	app.setup()
	frm = PreferenceDialog()
	frm.show()
	app.start()
	
