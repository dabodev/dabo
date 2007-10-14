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
from dabo.lib.connParser import createXML
from dabo.lib.connParser import importConnections
import dabo.lib.utils as utils
dui.loadUI("wx")



class EditorForm(dui.dForm):
	def afterSetMenuBar(self):
		self.createMenu()
		
		
	def afterInit(self):
		self.newFileName = "Untitled"
		self.fileExtension = "cnxml"
		self.defDbPorts = {"MySQL" : 3306,
				"Firebird" : 3050,
				"PostgreSQL" : 5432,
				"MsSQL" : 1433,
				"SQLite" : None }
		connKeys = ["host", "dbtype", "port", "database", "user", "password"]
		self.connDict = dict.fromkeys(connKeys)
		self._origConnDict = dict.fromkeys(connKeys)
		self.currentConn = None
		self.crypt = dabo.db.dConnectInfo()
		self.createControls()

		# temp hack to be polymorphic with dEditor (dIDE):
		self.editor = self

	
	def createMenu(self):
		mb = self.MenuBar
		fm = mb.getMenu("File")
		fm.prepend(_("Open Connection File..."), HotKey="Ctrl+O", OnHit=self.onOpenFile)
	
	
	def onOpenFile(self, evt):
		self.openFile()
	
	
	def createControls(self):
		self.Caption = "Connection Editor"
		self.Size= (500, 800)
		self.bg = dui.dPanel(self, BackColor="LightSteelBlue")
		
		gbsz = dui.dGridSizer(VGap=12, HGap=5, MaxCols=2)
		
		# Add the fields
		# Connection Dropdown
		cap = dui.dLabel(self.bg, Caption="Connection")
		ctl = dui.dDropdownList(self.bg, Choices=[""], 
				RegID="connectionSelector")
		ctl.bindEvent(dEvents.Hit, self.onConnectionChange)
		btn = dui.dButton(self.bg, Caption="Edit Name", RegID="cxnEdit")
		hsz = dui.dSizer("h")
		hsz.append(ctl)
		hsz.appendSpacer(10)
		hsz.append(btn)

		btn = dui.dButton(self.bg, Caption="Delete This Connection", RegID="cxnDelete",
				DynamicEnabled=self.hasMultipleConnections)
		hsz.appendSpacer(10)
		hsz.append(btn)

		gbsz.append(cap, halign="right", valign="middle")
		gbsz.append(hsz, valign="middle")
		
		# Backend Type
		cap = dui.dLabel(self.bg, Caption="Database Type")
		ctl = dui.dDropdownList(self.bg, RegID="DbType", 
				Choices=["MySQL", "Firebird", "PostgreSQL", "MsSQL", "SQLite"], 
				DataSource="form", DataField="dbtype")
		gbsz.append(cap, halign="right")
		gbsz.append(ctl)
		self.dbTypeSelector = ctl
		
		# Host
		cap = dui.dLabel(self.bg, Caption="Host")
		ctl = dui.dTextBox(self.bg, DataSource="form", DataField="host")
		gbsz.append(cap, halign="right")
		gbsz.append(ctl, "expand")
		self.hostText = ctl
		
		# Port
		cap = dui.dLabel(self.bg, Caption="Port")
		ctl = dui.dTextBox(self.bg, DataSource="form", DataField="port")
		gbsz.append(cap, halign="right")
		gbsz.append(ctl, "expand")
		self.portText = ctl
		
		# Database
		cap = dui.dLabel(self.bg, Caption="Database")
		ctl = dui.dTextBox(self.bg, DataSource="form", DataField="database")
		hsz = dui.dSizer("h")
		self.btnDbSelect = dui.dButton(self.bg, Caption=" ... ", RegID="btnDbSelect",
				Visible=False)
		hsz.append1x(ctl)
		hsz.appendSpacer(2)
		hsz.append(self.btnDbSelect, 0, "x")
		gbsz.append(cap, halign="right")
		gbsz.append(hsz, "expand")
		self.dbText = ctl
		
		# Username
		cap = dui.dLabel(self.bg, Caption="User Name")
		ctl = dui.dTextBox(self.bg, DataSource="form", DataField="user")
		gbsz.append(cap, halign="right")
		gbsz.append(ctl, "expand")
		self.userText = ctl
		
		# Password
		cap = dui.dLabel(self.bg, Caption="Password")
		ctl = dui.dTextBox(self.bg, PasswordEntry=True, 
				DataSource="form", DataField="password")
		gbsz.append(cap, halign="right")
		gbsz.append(ctl, "expand")
		self.pwText = ctl

		# Open Button
		btnSizer1 = dui.dSizer("h")
		btnSizer2 = dui.dSizer("h")
		btnTest = dui.dButton(self.bg, RegID="btnTest", Caption="Test...")
		btnSave = dui.dButton(self.bg, RegID="btnSave", Caption="Save")
		btnNewConn = dui.dButton(self.bg, RegID="btnNewConn", 
				Caption="New Connection")
		btnNewFile = dui.dButton(self.bg, RegID="btnNewFile", 
				Caption="New File")
		btnOpen = dui.dButton(self.bg, RegID="btnOpen", 
				Caption="Open File...")
		btnSizer1.append(btnTest, 0, border=3)
		btnSizer1.append(btnSave, 0, border=3)
		btnSizer2.append(btnNewConn, 0, border=3)
		btnSizer2.append(btnNewFile, 0, border=3)
		btnSizer2.append(btnOpen, 0, border=3)
		
		gbsz.setColExpand(True, 1)
		self.gridSizer = gbsz
		
		self.bg.Sizer = dui.dSizer("v")
		self.bg.Sizer.append(gbsz, 0, "expand", halign="center", border=20)
		self.bg.Sizer.append(btnSizer1, 0, halign="center")
		self.bg.Sizer.append(btnSizer2, 0, halign="center")
		self.Sizer = dui.dSizer("h")
		self.Sizer.append(self.bg, 1, "expand", halign="center")
		self.Layout()


	def hasMultipleConnections(self):
		return len(self.connDict.keys()) > 1
	
	
	def onHit_cxnDelete(self, evt):
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
		self.updtToForm()
		self.enableControls()
		self.update()
			
		
	def onHit_cxnEdit(self, evt):
		chc = self.connectionSelector.Choices
		idx = self.connectionSelector.PositionValue
		orig = chc[idx]
		new = dui.getString(_("Enter the name for the connection"), 
				caption="Connection Name", defaultValue=orig)
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
				

	def onHit_btnTest(self, evt):
		self.testConnection()
	
	
	def onHit_btnOpen(self, evt):
		# Update the values
		self.updtFromForm()
		# Now open the file
		self.openFile()
	
	
	def onHit_btnNewFile(self, evt):
		# Update the values
		self.updtFromForm()
		# See if the user wants to save changes (if any)
		if not self.confirmChanges():
			return
		self.newFile()
		
	
	def onHit_btnNewConn(self, evt):
		# Update the values
		self.updtFromForm()
		# Create the new connection
		self.newConnection()
		
		
	def onHit_btnSave(self, evt):
		self.saveFile()
		
		
	def onValueChanged_DbType(self, evt):
		# Update the values
		self.updtFromForm()
		self.enableControls()
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
		self.layout()
			
		if self.defDbPorts[dbt] is None:
			self.port = ""
		else:
			self.port = self.defDbPorts[dbt]

	
	def onHit_btnDbSelect(self, evt):
		dbFile = dui.getFile()
		if dbFile:
			self.database = dbFile
		self.update()
	

	def onHit_connectionSelector(self, evt):
		self.currentConn = self.connectionSelector.StringValue		
		self.updtToForm()
		self.enableControls()
		self.update()
		
	
	def testConnection(self):
		# Update the values
		self.updtFromForm()
		# Create a connection object.
		ci = dabo.db.dConnectInfo(connInfo=self.connDict[self.currentConn])
		try:
			conn = ci.getConnection()
			conn.close()
		except:
			conn = None
		
		if conn:
			msg = _("The connection was successful!")
			mb = dui.info
		else:
			msg = _("Unable to make connection")
			mb = dui.stop
		mb(message=msg, title="Connection Test")
	
	
	def updtFromForm(self):
		""" Grab the current values from the form, and update
		the connection dictionary with them.
		"""
		# Make sure that changes to the current control are used.
		self.activeControlValid()
		if self.currentConn is not None:
			dd = self.connDict[self.currentConn]
			for fld in dd.keys():
				val = eval("self.%s" % fld)
				if fld == "password":
					origVal = self.crypt.decrypt(dd[fld])
				else:
					origVal = dd[fld]
				if val == origVal:
					continue
				if fld == "password":
					dd[fld] = self.crypt.encrypt(val)
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
					val = self.crypt.decrypt(dd[fld])
				else:
					val = dd[fld]
				if isinstance(val, basestring):
					val = self.escQuote(val)		# Add quotes
				exec("self.%s = %s" % (fld, val) )

	
	def escQuote(self, val):
		"""Escape backslashes and single quotes, and wrap the result in single quotes."""
		sl = "\\"
		qt = "\'"
		return qt + val.replace(sl, sl+sl).replace(qt, sl+qt) + qt


	def newFile(self):
		self.connFile = self.newFileName
		self.connDict = {}
		# Set the form caption
		self.Caption = "Dabo Connection Editor: %s" % os.path.basename(self.connFile)
		# Add a new blank connection
		self.newConnection()
		self._origConnDict = copy.deepcopy(self.connDict)		
		# Fill the controls
		self.populate()

	
	def newConnection(self):
		# Update the values
		self.updtFromForm()
		newName = "Connection " + str(len(self.connDict.keys()) + 1)
		self.connDict[newName] = {
				"dbtype" : u"MySQL",
				"name" : "",
				"host" : "",
				"database" : "",
				"user" : "",
				"password" : "",
				"port" : 3306
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
				if val != self.crypt.decrypt(dd["password"]):
					dd[fld] = self.crypt.encrypt(val)
			else:
				dd[fld] = val
		except StandardError, e:
			print "Can't update:", e

	
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
				dabo.errorLog.write("The connection file '%s' does not exist." % self.connFile)
				self.connFile = None
				
		if self.connFile is None:
			f = dui.getFile(self.fileExtension, message="Select a file...", 
			defaultPath=os.getcwd() )
			if f is not None:
				self.connFile = f
			
		if self.connFile is not None:
			self.connFile = str(self.connFile)
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
			self.populate()
			self.layout()
			return True
		else:
			return False
		
		
	def confirmChanges(self):
		self.activeControlValid()
		self.updtFromForm()
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
			pth = dui.getSaveAs(message="Save File As...", 
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
		# Get the values from the connDict, and adjust any pathing
		# to be relative
		vals = self.relPaths(self.connDict.values())
		xml = createXML(vals)
		open(self.connFile, "w").write(xml)
		dabo.ui.callAfter(self.bringToFront)
	
	
	def relPaths(self, vals):
		for val in vals:
			if self.isFileBasedBackend(val["dbtype"]):
				db = val["database"]
				if os.path.exists(db):
					val["database"] = utils.relativePath(db, self.connFile)
		return vals
	
	
	
def main():
	files = sys.argv[1:]
	app = dabo.dApp()
	app.BasePrefKey = "CxnEditor"
	app.MainFormClass = None
	app.setup()
	app.start()
			
	if len(files) == 0:
		# The form can either edit a new file, or the user can open the file
		# from the form
		o = EditorForm()
		o.newFile()
		o.Show()
	else:
		for file in files:
			o = EditorForm()
			o.openFile(file)
			if o.connFile:
				o.Show()
			else:
				o.Close()
			
	app.start()
	
	
if __name__ == "__main__":
	main()	
