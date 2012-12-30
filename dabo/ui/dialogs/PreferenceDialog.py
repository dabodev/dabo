# -*- coding: utf-8 -*-
import sys
import os
import inspect
import dabo.ui
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
from dabo.dLocalize import _
from dabo.ui.dialogs.HotKeyEditor import HotKeyEditor
from dabo.lib.utils import cleanMenuCaption

dayMins= 24*60



class PreferenceDialog(dabo.ui.dOkCancelDialog):
	def _afterInit(self):
		self._includeDefaultPages = True
		update = dabo.checkForWebUpdates
		if update:
			# If they are running Subversion, don't update.
			if os.path.isdir(os.path.join(os.path.split(dabo.__file__)[0], ".svn")):
				update = False
			# Frozen App:
			if hasattr(sys, "frozen") and inspect.stack()[-1][1] != "daborun.py":
				update = False
		self._includeFrameworkPages = update
		self.Size = (700, 600)
		self.AutoSize = False
		self.Caption = _("Preferences")
		# Set up a list of functions to call when the user clicks 'OK' to accept changes,
		# and one for functions to call when the user cancels.
		self.callOnAccept = []
		self.callOnCancel = [self.onRollbackMenuChanges]
		# Create a list of preference key objects that will be have their AutoPersist turned
		# off when the dialog is shown, and either canceled or persisted, depending
		# on the user's action.
		self.preferenceKeys = []
		super(PreferenceDialog, self)._afterInit()


	def addControls(self):
		"""
		Add the base PageList, and then delete this method from the
		namespace. Users will customize with addCategory() and then
		adding controls to the category page.
		"""
		self._addPages()
		dabo.ui.callAfter(self.update)
		self.layout()
		# Use this to 'delete' addControls() so that users don't try to use this method.
		self.addControls = None


	def _addPages(self):
#		self.pgfMain = dabo.ui.dPageList(self, TabPosition="Left",
# 				ListSpacing=20)
		self.pgfMain = dabo.ui.dPageFrame(self, TabPosition="Top")
		self.addPages()
		incl = (self.pgfMain.PageCount == 0)
		if incl or self.IncludeDefaultPages:
			self._addDefaultPages()
		incl = (self.pgfMain.PageCount == 0)
		if incl or self.IncludeFrameworkPages:
			self._addFrameworkPages()
		self.Sizer.append1x(self.pgfMain)
		self.update()
		self.layout()


	def addPages(self): pass


	def appendPage(self, pgCls=None, *args, **kwargs):
		"""Pass-through method to the internal paged control"""
		return self.pgfMain.appendPage(pgCls, *args, **kwargs)


	def insertPage(self, pos, pgCls=None, *args, **kwargs):
		"""Pass-through method to the internal paged control"""
		return self.pgfMain.insertPage(pos, pgCls, *args, **kwargs)


	def _onAcceptPref(self):
		"""
		This is called by the app when the user clicks the OK button. Every method in
		the callOnAccept list is called, followed by a call to the user-configurable
		onAccept() method.
		"""
		self.activeControlValid()
		for fnc in self.callOnAccept:
			fnc()
		# Call the user-configurable method
		self.onAcceptPref()


	def onAcceptPref(self):
		"""Override this for subclasses where you need separate OK processing."""
		pass


	def _onCancelPref(self):
		"""
		This is called by the app when the user clicks the Cancel button. Every method
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
		"""
		Adds a page to the main PageList control, sets the caption to the
		passed string, and returns a reference to the page. If the optional 'pos'
		parameter is passed, the page is inserted in that position; otherwise, it
		is appended after any existing pages.
		"""
		if pos is None:
			pos = self.pgfMain.PageCount
		return self.pgfMain.insertPage(pos, caption=category)


	def _addDefaultPages(self):
		"""
		Called when no other code exists to fill the dialog, or when
		the class's IncludeDefaultPages property is True.
		"""
		af = self.Application.ActiveForm
		if not af or af is self:
			af = self.Parent
		try:
			mb = af.MenuBar
		except AttributeError:
			mb = None
		if mb:
			pm = af.PreferenceManager.menu
			self.preferenceKeys.append(pm)
			menuPage = self.pgMenuKeys = self.addCategory(_("Menu Keys"))
			self._selectedItem = None
			self._hotKeyMap = {}
			menuPage.Sizer.Orientation = "H"
			tree = dabo.ui.dTreeView(menuPage, OnTreeSelection=self._onMenuTreeSelection,
					RegID="menuKeyAssignmentTree")
			root = tree.setRootNode(_("Menu"))
			for mn in mb.Children:
				cap = cleanMenuCaption(mn.Caption, "&")
				prefcap = cleanMenuCaption(mn.Caption)
				nd = root.appendChild(cap)
				nd.pref = pm
				nd.hotkey = "n/a"
				nd.Object = mn
				menukey = pm.get(prefcap)
				self._recurseMenu(mn, nd, menukey)
			menuPage.Sizer.append1x(tree, border=10)
			root.expand()
			self._originalHotKeyMap = self._hotKeyMap.copy()

			sz = dabo.ui.dGridSizer(MaxCols=2, HGap=5, VGap=10)
			lbl = dabo.ui.dLabel(menuPage, Caption=_("Current Key:"))
			txt = dabo.ui.dTextBox(menuPage, ReadOnly=True, Alignment="Center",
					RegID="txtMenuCurrentHotKey")
			sz.append(lbl, halign="right")
			sz.append(txt, "x")
			sz.appendSpacer(1)
			btn = dabo.ui.dButton(menuPage, Caption=_("Set Key..."),
					OnHit=self._setHotKey, DynamicEnabled=self._canSetHotKey)
			sz.append(btn, halign="center")
			sz.appendSpacer(1)
			btn = dabo.ui.dButton(menuPage, Caption=_("Clear Key"),
					OnHit=self._clearHotKey, DynamicEnabled=self._canClearHotKey)
			sz.append(btn, halign="center")
			sz.setColExpand(True, 1)
			menuPage.Sizer.append1x(sz, border=10)


	def _recurseMenu(self, mn, nd, pref):
		"""mn is the menu; nd is the tree node for that menu; pref is the pref key for the menu."""
		for itm in mn.Children:
			native = True
			try:
				cap = cleanMenuCaption(itm.Caption, "&")
				prefcap = cleanMenuCaption(itm.Caption)
			except AttributeError:
				# A separator line
				continue
			kidnode = nd.appendChild(cap)
			subpref = pref.get(prefcap)
			kidnode.pref = subpref
			kidnode.hotkey = "n/a"
			if itm.Children:
				self._recurseMenu(itm, kidnode, subpref)
			else:
				try:
					kidnode.hotkey = itm.HotKey
					self._hotKeyMap[itm.HotKey] = itm
				except AttributeError:
					pass
				kidnode.Object = itm


	def _onMenuTreeSelection(self, evt):
		self._selectedItem = nd = evt.selectedNode
		if nd:
			if nd.IsRootNode:
				return
			if nd.hotkey == "n/a":
				self.txtMenuCurrentHotKey.Value = ""
			else:
				self.txtMenuCurrentHotKey.Value = nd.hotkey
		self.update()


	def _setHotKey(self, evt):
		dlg = HotKeyEditor(self)
		itm = self._selectedItem
		origKey = itm.hotkey
		dlg.setKey(origKey)
		dlg.show()
		if dlg.Accepted:
			hk = dlg.KeyText
			change = (hk != origKey)
			dupeItem = None
			if change:
				dupeItem = self._hotKeyMap.get(hk)
				if dupeItem and (dupeItem is not itm):
					msg = _("This key combination is assigned to the menu command '%s'. " +
							"Do you wish to re-assign it to the command '%s'?") % (cleanMenuCaption(dupeItem.Caption, "&_"),
							cleanMenuCaption(itm.Caption, "&_"))
					change = dabo.ui.areYouSure(msg, title=_("Duplicate Keystroke"), defaultNo=True,
							cancelButton=False)
			if change:
				if dupeItem:
					# Un-assign that hotkey
					dupeItem.HotKey = None
					# Clear it from the tree
					nd = self.menuKeyAssignmentTree.nodeForObject(dupeItem)
					if nd:
						nd.hotkey = None
				if origKey:
					self._hotKeyMap.pop(origKey)
				if hk:
					# Set the internal key map.
					self._hotKeyMap[hk] = itm.Object
				self.txtMenuCurrentHotKey.Value = itm.hotkey = itm.Object.HotKey = hk
				itm.pref.setValue("hotkey", hk)
		dlg.release()
		self.pgMenuKeys.update()


	def _canSetHotKey(self):
		itm = self._selectedItem
		return (itm is not None) and (itm.hotkey != "n/a")


	def _clearHotKey(self, evt):
		itm = self._selectedItem
		self._hotKeyMap.pop(itm.hotkey)
		self.txtMenuCurrentHotKey.Value = itm.hotkey = itm.Object.HotKey = None
		itm.pref.setValue("hotkey", None)
		self.pgMenuKeys.update()

	def _canClearHotKey(self):
		itm = self._selectedItem
		return (itm is not None) and (itm.hotkey not in ("n/a", None))


	def onRollbackMenuChanges(self):
		km = self._originalHotKeyMap
		for key in km.keys():
			km[key].HotKey = key


	def _addFrameworkPages(self):
		"""
		Called when no other code exists to fill the dialog, or when
		the class's IncludeFrameworkPages property is True.
		"""
		wuPage = self.pgWebUpdate = self.addCategory(_("Web Update"))
		# Set the framework-level pref manager
		fp = self.Application._frameworkPrefs
		# Make sure that there is an update frequency pref
		update_choices = [_("Every time an app is run"), _("Once a day"), _("Once a week"), _("Once a month")]
		update_keys = [0, dayMins, dayMins*7, dayMins*30]
		freq = fp.update_interval
		if freq not in update_keys:
			fp.update_interval = dayMins
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
				Choices=update_choices, Keys=update_keys,
				ValueMode="Keys", DataSource=fp, DataField="update_interval",
				ToolTipText=_("How often does the framework check for updates?"),
				DynamicEnabled = lambda: self.chkForWebUpdates.Value)
		sz.append(radFrequency, halign="center")


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


	def _getIncludeFrameworkPages(self):
		return self._includeFrameworkPages

	def _setIncludeFrameworkPages(self, val):
		if self._constructed():
			self._includeFrameworkPages = val
		else:
			self._properties["IncludeFrameworkPages"] = val


	IncludeDefaultPages = property(_getIncludeDefaultPages, _setIncludeDefaultPages, None,
			_("""When True, the _addDefaultPages() method is called to add the common
			Dabo settings. Default=True  (bool)"""))

	IncludeFrameworkPages = property(_getIncludeFrameworkPages, _setIncludeFrameworkPages, None,
			_("""When True, the _addFrameworkPages() method is called to add the common
			Dabo settings. Default=False  (bool)"""))


if __name__ == "__main__":
	from dabo.dApp import dApp
	class TestForm(dabo.ui.dForm):
		def afterInit(self):
			lbl = dabo.ui.dLabel(self, Caption="Preference Manager Demo\n" +
				"Select 'Preferences' from the menu.", WordWrap=True)
			self.Sizer.append(lbl, halign="center", border=20)

	app = dApp(MainFormClass=TestForm)
	app.start()

