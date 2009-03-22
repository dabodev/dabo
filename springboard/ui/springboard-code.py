# -*- coding: utf-8 -*-
### Dabo Class Designer code. You many freely edit the code,
### but do not change the comments containing:
### 		'Dabo Code ID: XXXX', 
### as these are needed to link the code to the objects.

import os
import time
import urlparse
import re
import dabo
from dabo.lib.RemoteConnector import RemoteConnector
from dabo.dLocalize import _


## *!* ## Dabo Code ID: dTextBox-dPanel
def onKeyChar(self, evt):
	if evt.keyCode == dabo.ui.dKeys.key_Return:
		mthd = self.Form.connectToServer
	else:
		mthd = self.Form.completeURL
	dabo.ui.callAfter(mthd, key=evt.keyCode)



## *!* ## Dabo Code ID: dListBox-dPanel
def afterInit(self):
	self.bindKey("enter", self.onEnter)
	self.bindEvent(dabo.dEvents.MouseLeftDoubleClick, self.onEnter)


def onEnter(self, evt):
	self.Form.runSelection()



## *!* ## Dabo Code ID: dButton-dPanel-553
def afterInit(self):
	self.DynamicEnabled = self.Form.hasSelection


def onHit(self, evt):
	self.Form.runSelection()



## *!* ## Dabo Code ID: dForm-top
def _getAddress(self):
	try:
		addr = self.txtAddress.Value
	except AttributeError:
		return None
	if not re.match("https?://.*", addr):
		addr = "http://%s" % addr
	return addr


def _runApp(self, path):
	app = os.path.split(path)[1]
	self.busy = dabo.ui.busyInfo(_("Launching the '%s' application...") % app)
	appdir = self._proxy.syncFiles(path)
	if appdir:
		os.chdir(appdir)
	# We'll assume that the main program is 'main.py'
	main = [fname for fname in ("main.py", "%s.py" % app, "go.sh")
			if os.path.exists(fname)]
	if main:
		# Use the first, in case there are more than one 'main' program
		pid, proc = dabo.ui.spawnProcess("/usr/bin/python %s" % main[0], handler=self)
		self._processes.append(proc)
		
		def setNone():
			self.busy = None
		dabo.ui.callAfterInterval(2000, setNone)


# def onIdle(self, evt):
# 	for proc in self._processes:
# 		if not proc:
# 			continue
# 		else:
# 			print "PROC", proc.read()

def onProcTermintated(self, proc, pid, status):
	self._processes.remove(proc)


def afterInit(self):
	self._escChar = "|||"
	self._proxy = RemoteConnector(self)
	self._availableApps = []
	self._processes = []


def afterInitAll(self):
	self.mrus = []
	recent = None
	choices = []
	prefMRU = self.PreferenceManager.mru
	mrus = prefMRU.getPrefKeys()
	if mrus:
		mrus.sort()
		while mrus:
			mruKey = mrus.pop()
			mru = prefMRU.get(mruKey)
			if isinstance(mru, basestring):
				choices.append(mru)
				if not recent:
					recent = mru
		self.mrus = choices
	if not recent:
		# First time; add a default value
		recent = "http://"
	self.txtAddress.Value = recent
	self.update()
	dabo.ui.callAfter(self.initialFocus)


def initialFocus(self):
	txt = self.txtAddress
	txt.setFocus()
	addr = txt.Value
	slashpos = addr.find("//")
	if slashpos >= 0:
		txt.SelectionStart = slashpos + 2
		txt.SelectionEnd = len(addr)


def completeURL(self, key=None):
	deleting = key in (dabo.ui.dKeys.key_Back, dabo.ui.dKeys.key_Delete)
	txt = self.txtAddress
	addr = txt.Value
	if deleting:
		addr = addr[:-1]
	addrLen = len(addr)
	matches = [mru for mru in self.mrus
			if mru.startswith(addr)]
	if matches and not deleting:
		txt.Value = matches[0]
		txt.SelectionStart = addrLen
		txt.SelectionEnd = 999


def connectToServer(self, key=None):
	addr = self.Address
	if not addr:
		dabo.ui.stop("Please enter the address of the server.")
		self.txtAddress.setFocus()
		return
	try:
		result = self._proxy.launch(url=addr)
	except StandardError, e:
		print "CONNECTION ERR", type(e), e
		return
	if result:
		# Add to MRUS
		self._addToMRUs(addr)
		if isinstance(result, basestring) and result.startswith("Error"):
			# Error
			dabo.ui.stop(result, "Server Error")
		elif isinstance(result, list):
			self.appList.Choices = result
			self.appList.PositionValue = 0
			self.update()
			dabo.ui.callAfter(self.appList.setFocus)
			self.refresh()
		elif isinstance(result, basestring) and result.startswith("404"):
			dabo.ui.stop(_("%s\nAre you sure that's a Dabo application server?") % addr, result)
		else:
			dabo.ui.stop(_("Received this message from the server: %s") % str(result), _("Server Error"))


def _addToMRUs(self, addr):
	# Add to MRU
	stamp = "%s" % int(round(time.time() * 100, 0))
	prefMRU = self.PreferenceManager.mru
	scheme, netloc, path, parameters, query, fragment = urlparse.urlparse(addr)
	stored = "%s://%s" % (scheme, netloc)
	prefMRU.deleteByValue(stored)
	prefMRU.setValue(stamp, stored)

def hasSelection(self):
	return bool(self.appList.Choices and self.appList.Value)


def runSelection(self):
	app = self.appList.Value
	if not app:
			dabo.ui.stop(_("Please select an application"))
			return
	# Add it to the MRUs
	scheme, netloc, path, parameters, query, fragment = urlparse.urlparse(self.Address)
	stored = "%s://%s" % (scheme, netloc)
	stamp = "%s" % int(round(time.time() * 100, 0))
	prefMRU = self.PreferenceManager.mru
	prefMRU.deleteByValue(stored)
	prefMRU.setValue(stamp, stored)
	self._runApp(app)



## *!* ## Dabo Code ID: dButton-dPanel
def onHit(self, evt):
	self.Form.connectToServer()
