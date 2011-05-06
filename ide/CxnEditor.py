#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import copy
import dabo
import dabo.ui as dui
import dabo.dEvents as dEvents
import dabo.dConstants as k
from dabo.dLocalize import _
from dabo.lib.utils import ustr
from dabo.lib.connParser import createXML
from dabo.lib.connParser import importConnections
import dabo.lib.utils as utils
dui.loadUI("wx")
from HomeDirectoryStatusBar import HomeDirectoryStatusBar



class EditorForm(dui.dForm):
	def afterSetMenuBar(self):
		self.createMenu()


	def beforeInit(self):
		self.StatusBarClass = HomeDirectoryStatusBar


	def afterInit(self):
		self.Size = (600, 400)
		self.newFileName = "Untitled"
		self.fileExtension = "cnxml"
		self.defDbPorts = {"MySQL" : 3306,
				"Firebird" : 3050,
				"PostgreSQL" : 5432,
				"MsSQL" : 1433,
				"SQLite" : None }
		connKeys = ["name", "host", "dbtype", "port", "database", "user", "password"]
		# Make sure that they are defined as form attributes
		for ck in connKeys:
			setattr(self, ck, None)
		self.connDict = dict.fromkeys(connKeys)
		self._origConnDict = dict.fromkeys(connKeys)
		self.currentConn = None
		# If we're opening a cnxml file that was saved with a CryptoKey, this
		# flag will indicate that the user should be prompted.
		self._opening = False
		# all set up; now add stuff!
		self.createControls()

		# temp hack to be polymorphic with dEditor (dIDE):
		self.editor = self


	def createMenu(self):
		mb = self.MenuBar
		fm = mb.getMenu("base_file")
		fm.prepend(_("Open Connection File..."),
				HotKey="Ctrl+O",
				OnHit=self.onOpenFile,
				ItemID="file_open",
				help=_("Open an existing connection file"))


	def onOpenFile(self, evt):
		self.openFile()


	def createControls(self):
		self.Caption = _("Connection Editor")
		self.bg = dui.dPanel(self, BackColor="LightSteelBlue")
		gbsz = dui.dGridSizer(VGap=12, HGap=5, MaxCols=2)

		# Add the fields
		# Connection Dropdown
		cap = dui.dLabel(self.bg, Caption=_("Connection"))
		ctl = dui.dDropdownList(self.bg, Choices=[""],
				RegID="connectionSelector",
				OnHit=self.onConnectionChange)
		btn = dui.dButton(self.bg, Caption=_("Edit Name"), RegID="cxnEdit",
				OnHit=self.onCxnEdit)
		hsz = dui.dSizer("h")
		hsz.append(ctl)
		hsz.appendSpacer(10)
		hsz.append(btn)

		btn = dui.dButton(self.bg, Caption=_("Delete This Connection"), RegID="cxnDelete",
				DynamicEnabled=self.hasMultipleConnections,
				OnHit=self.onCxnDelete)
		hsz.appendSpacer(10)
		hsz.append(btn)

		gbsz.append(cap, halign="right", valign="middle")
		gbsz.append(hsz, valign="middle")

		# Backend Type
		cap = dui.dLabel(self.bg, Caption=_("Database Type"))
		ctl = dui.dDropdownList(self.bg, RegID="DbType",
				Choices=["MySQL", "Firebird", "PostgreSQL", "MsSQL", "SQLite"],
				DataSource="form", DataField="dbtype",
				OnHit=self.onDbTypeChanged)
		gbsz.append(cap, halign="right")
		gbsz.append(ctl)
		self.dbTypeSelector = ctl

		# Host
		cap = dui.dLabel(self.bg, Caption=_("Host"))
		ctl = dui.dTextBox(self.bg, DataSource="form", DataField="host")
		gbsz.append(cap, halign="right")
		gbsz.append(ctl, "expand")
		self.hostText = ctl

		# Port
		cap = dui.dLabel(self.bg, Caption=_("Port"))
		ctl = dui.dTextBox(self.bg, DataSource="form", DataField="port")
		gbsz.append(cap, halign="right")
		gbsz.append(ctl, "expand")
		self.portText = ctl

		# Database
		cap = dui.dLabel(self.bg, Caption=_("Database"))
		ctl = dui.dTextBox(self.bg, DataSource="form", DataField="database")
		hsz = dui.dSizer("h")
		self.btnDbSelect = dui.dButton(self.bg, Caption=" ... ", RegID="btnDbSelect",
				Visible=False, OnHit=self.onDbSelect)
		hsz.append1x(ctl)
		hsz.appendSpacer(2)
		hsz.append(self.btnDbSelect, 0, "x")
		gbsz.append(cap, halign="right")
		gbsz.append(hsz, "expand")
		self.dbText = ctl

		# Username
		cap = dui.dLabel(self.bg, Caption=_("User Name"))
		ctl = dui.dTextBox(self.bg, DataSource="form", DataField="user")
		gbsz.append(cap, halign="right")
		gbsz.append(ctl, "expand")
		self.userText = ctl

		# Password
		cap = dui.dLabel(self.bg, Caption=_("Password"))
		ctl = dui.dTextBox(self.bg, PasswordEntry=True,
				DataSource="form", DataField="password")
		gbsz.append(cap, halign="right")
		gbsz.append(ctl, "expand")
		self.pwText = ctl

		# Open Button
		btnSizer1 = dui.dSizer("h")
		btnSizer2 = dui.dSizer("h")
		btnTest = dui.dButton(self.bg, RegID="btnTest", Caption=_("Test..."),
				OnHit=self.onTest)
		btnSave = dui.dButton(self.bg, RegID="btnSave", Caption=_("Save"),
				OnHit=self.onSave)
		btnNewConn = dui.dButton(self.bg, RegID="btnNewConn",
				Caption=_("New Connection"),
				OnHit=self.onNewConn)
		btnNewFile = dui.dButton(self.bg, RegID="btnNewFile",
				Caption=_("New File"),
				OnHit=self.onNewFile)
		btnOpen = dui.dButton(self.bg, RegID="btnOpen",
				Caption=_("Open File..."),
				OnHit=self.onOpen)
		btnSizer1.append(btnTest, 0, border=3)
		btnSizer1.append(btnSave, 0, border=3)
		btnSizer2.append(btnNewConn, 0, border=3)
		btnSizer2.append(btnNewFile, 0, border=3)
		btnSizer2.append(btnOpen, 0, border=3)
		gbsz.setColExpand(True, 1)
		self.gridSizer = gbsz

		sz = self.bg.Sizer = dui.dSizer("v")
		sz.append(gbsz, 0, "expand", halign="center", border=20)
		sz.append(btnSizer1, 0, halign="center")
		sz.append(btnSizer2, 0, halign="center")
		# Only create the 'Set Crypto Key' button if PyCrypto is installed
		try:
			from Crypto.Cipher import DES3 as _TEST_DES3
			self._showKeyButton = True
			del _TEST_DES3
		except ImportError:
			self._showKeyButton = False
		if self._showKeyButton:
			self.cryptoKeyButton = dui.dButton(self.bg, Caption=_("Set Crypto Key"),
					OnHit=self.onSetCrypto)
			btnSizer1.append(self.cryptoKeyButton, 0, halign="center", border=3)
		self.Sizer = dui.dSizer("h")
		self.Sizer.append(self.bg, 1, "expand", halign="center")
		self.Layout()


	def hasMultipleConnections(self):
		return len(self.connDict.keys()) > 1


	def onCxnDelete(self, evt):
		if not dabo.ui.areYouSure(_("Delete this connection?"),
				title=_("Confirm Deletion"), cancelButton=False):
			return
		cs = self.connectionSelector
		delkey = cs.StringValue
		pos = cs.PositionValue
		del self.connDict[delkey]
		cs.Choices = self.connDict.keys()
		cs.PositionValue = min(pos, len(self.connDict.keys())-1)
		self.currentConn = cs.StringValue
		self.enableControls()
		self.updtToForm()
		self.update()


	def onCxnEdit(self, evt):
		chc = self.connectionSelector.Choices
		idx = self.connectionSelector.PositionValue
		orig = chc[idx]
		new = dui.getString(_("Enter the name for the connection"),
				caption=_("Connection Name"), defaultValue=orig)
		if new is not None:
			if new != orig:
				chc[idx] = new
				self.connectionSelector.Choices = chc
				# Update the connection dict, too
				oldVal = self.connDict[orig]
				self.connDict[new] = oldVal
				del self.connDict[orig]
				self.connDict[new]["name"] = new
				self.currentConn = new
				self.name = new
			self.connectionSelector.PositionValue = idx


	def onSetCrypto(self, evt):
		key = self._askForKey()
		if key:
			self.Application.CryptoKey = key
			# Need to re-encrypt the password
			self.updtFromForm()


	def _askForKey(self):
		ret = dabo.ui.getString(_("Enter the cryptographic key for your application"),
				caption=_("Crypto Key"), Width=240)
		return ret


	def onTest(self, evt):
		self.testConnection()


	def onOpen(self, evt):
		# Update the values
		self.updtFromForm()
		# Now open the file
		self.openFile()


	def onNewFile(self, evt):
		# Update the values
		self.updtFromForm()
		# See if the user wants to save changes (if any)
		if not self.confirmChanges():
			return
		self.newFile()


	def onNewConn(self, evt):
		# Update the values
		self.updtFromForm()
		# Create the new connection
		self.newConnection()


	def onSave(self, evt):
		self.saveFile()


	def onDbTypeChanged(self, evt):
		# Update the values
		self.updtFromForm()
		self.enableControls()
		if self.defDbPorts[self.dbtype] is None:
			self.port = ""
		else:
			self.port = self.defDbPorts[self.dbtype]
		self.update()


	def isFileBasedBackend(self, dbtype):
		return dbtype in ("SQLite", )


	def enableControls(self):
		dbt = self.dbtype
		isFileBased = self.isFileBasedBackend(dbt)
		self.hostText.Visible = not isFileBased
		self.portText.Visible = not isFileBased
		self.userText.Visible = not isFileBased
		self.pwText.Visible = not isFileBased
		self.btnDbSelect.Visible = isFileBased
		if isFileBased:
			self.dbText.setFocus()
		self.layout()


	def onDbSelect(self, evt):
		dbFile = dui.getFile()
		if dbFile:
			self.database = dbFile
		self.update()


	def testConnection(self):
		# Update the values
		self.updtFromForm()
		# Create a connection object.
		ci = dabo.db.dConnectInfo(connInfo=self.connDict[self.currentConn])
		mb = dui.stop
		mbTitle = _("Connection Test")
		try:
			conn = ci.getConnection()
			conn.close()
			msg = _("The connection was successful!")
			mb = dui.info
		except ImportError, e:
			msg = _("Python Import Error: %s") % e
			mbTitle += _(": FAILED!")
		except StandardError, e:
			msg = _("Could not connect to the database: %s") % e
			mbTitle += _(": FAILED!")
		mb(message=msg, title=mbTitle)


	def updtFromForm(self):
		""" Grab the current values from the form, and update
		the connection dictionary with them.
		"""
		# Make sure that changes to the current control are used.
		self.activeControlValid()
		if self.currentConn is not None:
			dd = self.connDict[self.currentConn]
			for fld in dd.keys():
				val = getattr(self, fld)
				if fld == "password":
					try:
						origVal = self.Crypto.decrypt(dd[fld])
					except ValueError:
						# Original crypto key not available
						origVal = None
				else:
					origVal = dd[fld]
				if val == origVal:
					continue
				if fld == "password":
					dd[fld] = self.Crypto.encrypt(val)
				else:
					dd[fld] = val


	def updtToForm(self):
		""" Populate the current values from the connection
		dictionary.
		"""
		if self.currentConn is not None:
			dd = self.connDict[self.currentConn]
			for fld in dd.keys():
				val = dd[fld]
				if fld == "password":
					try:
						val = self.Crypto.decrypt(dd[fld])
					except ValueError:
						# Original crypto key not available
						if self._opening and self._showKeyButton:
							dabo.ui.callAfter(self._getCryptoKey, dd[fld])
							continue
						else:
							val = ""
				else:
					val = dd[fld]
 				setattr(self, fld, val)


	def _getCryptoKey(self, crypted):
		# Give them a chance to set the CryptoKey
		val = ""
		key = self._askForKey()
		if key:
			self.Application.CryptoKey = key
			val = self.Crypto.decrypt(crypted)
		setattr(self, "password", val)


	def newFile(self):
		self.connFile = self.newFileName
		self.connDict = {}
		# Set the form caption
		self.Caption = _("Dabo Connection Editor: %s") % os.path.basename(self.connFile)
		# Add a new blank connection
		self.newConnection()
		self._origConnDict = copy.deepcopy(self.connDict)
		# Fill the controls
		self.populate()


	def newConnection(self):
		# Update the values
		self.updtFromForm()
		# Get the current dbtype
		if self.currentConn is not None:
			currDbType = self.connDict[self.currentConn]["dbtype"]
		else:
			currDbType = u"MySQL"
		newName = u"Connection_" + ustr(len(self.connDict.keys()) + 1)
		self.connDict[newName] = {
				"dbtype" : currDbType,
				"name" : newName,
				"host" : "",
				"database" : "",
				"user" : "",
				"password" : "",
				"port" : self.defDbPorts[currDbType]
				}
		self.currentConn = newName
		self.connectionSelector.Choices = self.connDict.keys()
		self.populate()


	def saveFile(self):
		self.updtFromForm()
		if self._origConnDict != self.connDict:
			self.writeChanges()
			self._origConnDict = copy.deepcopy(self.connDict)


	def onConnectionChange(self, evt):
		newConn = self.connectionSelector.StringValue
		if newConn != self.currentConn:
			# Update the values
			self.updtFromForm()
			self.currentConn = newConn
			self.populate()


	def setFieldVal(self, fld, val):
		""" This will get called when the control detects a changed value. We
		need to update the current dict with the new value.
		"""
		try:
			dd = self.connDict[self.currentConn]
			if fld == "password":
				if val != self.Crypto.decrypt(dd["password"]):
					dd[fld] = self.Crypto.encrypt(val)
			else:
				dd[fld] = val
		except StandardError, e:
			print _("Can't update:"), e


	def populate(self):
		self.updtToForm()
		self.update()
		conn = self.currentConn
		self.connectionSelector.Value = conn


	def openFile(self, connFile=None):
		self.activeControlValid()
		# See if the user wants to save changes (if any)
		if not self.confirmChanges():
			return
		self.connFile = connFile
		# Read in the connection def file
		if self.connFile:
			# Make sure that the passed file exists!
			if not os.path.exists(self.connFile):
				dabo.log.error(_("The connection file '%s' does not exist.") % self.connFile)
				self.connFile = None

		if self.connFile is None:
			f = dui.getFile(self.fileExtension, message=_("Select a file..."),
			defaultPath=os.getcwd() )
			if f is not None:
				self.connFile = f

		if self.connFile is not None:
			self.connFile = ustr(self.connFile)
			# Read the XML into a local dictionary
			self.connDict = importConnections(self.connFile)
			# Save a copy for comparison
			self._origConnDict = copy.deepcopy(self.connDict)
			# Populate the connection names
			self.connectionSelector.Choices = self.connDict.keys()
			# Set the current connection
			self.currentConn = self.connDict.keys()[0]
			# Set the form caption
			self.Caption = _("Dabo Connection Editor: %s") % os.path.basename(self.connFile)
			# Fill the controls
			self._opening = True
			self.populate()
			self._opening = False
			# Show/hide controls as needed
			self.enableControls()
			self.layout()
			return True
		else:
			return False


	def confirmChanges(self):
		self.activeControlValid()
		self.updtFromForm()
		if self._origConnDict != self.connDict:
			# Could be relative path differences
			self.relPaths(self.connDict.values())
		if self._origConnDict != self.connDict:
			response = dui.areYouSure(_("Do you wish to save your changes?"),
					cancelButton=True)
			if response is None:
				return False
			elif response:
				self.writeChanges()
		return True


	def writeChanges(self):
		if self.connFile == self.newFileName:
			# Ask for a file name
			pth = dui.getSaveAs(message=_("Save File As..."),
					wildcard=self.fileExtension)
			if pth is None:
				return
			else:
				pthName = os.path.basename(pth)
				if not pthName.split(".")[-1] == self.fileExtension:
					# Add the extension
					if pth[-1] != ".":
						pth += "."
					pth += self.fileExtension
				self.connFile = pth
		# Create the file so that the relative pathing works correctly
		file(self.connFile, "w")
		# Get the values from the connDict, and adjust any pathing
		# to be relative
		vals = self.relPaths(self.connDict.values())
		v0 = vals[0]
		if self.isFileBasedBackend(v0["dbtype"]):
			# Previous values from the form might still be in the dict.
			# Blank them out, as they are not valid for file-based backends.
			v0["host"] = v0["user"] = v0["password"] = v0["port"] = ""
		xml = createXML(vals, encoding="utf-8")
		file(self.connFile, "w").write(xml)
		dabo.ui.callAfter(self.bringToFront)


	def relPaths(self, vals):
		for val in vals:
			if self.isFileBasedBackend(val["dbtype"]):
				db = val["database"]
				if os.path.exists(db):
					val["database"] = utils.relativePath(db, self.Application.HomeDirectory)
		return vals


	def _getCrypto(self):
		try:
			return self.Application.Crypto
		except:
			pass


	Crypto = property(_getCrypto, None, None,
			_("A reference to the application-supplied encryption object (dabo.lib.SimpleCrypt)"))


def main():
	files = sys.argv[1:]
	app = dabo.dApp(ignoreScriptDir=True)
	app.BasePrefKey = "CxnEditor"
	app.MainFormClass = None
	app.setup()

	if len(files) == 0:
		# The form can either edit a new file, or the user can open the file
		# from the form
		o = EditorForm()
		o.newFile()
		o.show()
	else:
		for file in files:
			o = EditorForm()
			o.openFile(file)
			if o.connFile:
				o.show()
			else:
				o.close()

	app.start()


if __name__ == "__main__":
	main()
