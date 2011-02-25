# -*- coding: utf-8 -*-
"""
(Barely started - don't use)

Ed writes:

The whole threading issue. Since killing threads is not
feasible, we should look at what we want to accomplish.
Ideally, we want to avoid locking the UI by a runaway query
process. Given that, we should rewrite all potentially
runaway calls in the UI to the bizobj so that we begin by
creating a separate thread for the bizobj call. The UI then
starts a timer, which will display a "Please Wait" message
with a Cancel button after a given time (say, 1 second). If
the user clicks Cancel, the UI continues on its way. Further
interaction with the bizobj will not be possible until the
bizobj process returns, since its state will be undefined. We
then need a UI-level flag to be set to indicate this state.
The bizobj returns from its process by emitting an event; the
UI will have to trap that event, and if it is received when
the flag is set, issue a call to the bizobj to reset itself
back to its last known state. When the bizobj completes that,
the UI clears the 'unstable' flag. This will require, of
course, that the bizobj save its state before each call, and
be able to restore that state when asked. None of this will
eliminate problems caused by runaway queries, but will at
least allow the UI to remain responsive, reducing the chance
that the user will three-finger it.
"""
import time
from threading import *
import wx
import dabo
from dabo.dLocalize import _

ID_CANCEL = wx.NewId()
EVT_RESULT_ID = wx.NewId()
EVT_EXCEPTION_ID = wx.NewId()

def EVT_RESULT(win, func):
	win.Connect(-1, -1, EVT_RESULT_ID, func)

def EVT_EXCEPTION(win, func):
	win.Connect(-1, -1, EVT_EXCEPTION_ID, func)

class ResultEvent(wx.PyEvent):
	"""Simple event to carry arbitrary result data."""

	def __init__(self, response):
		wx.PyEvent.__init__(self)
		self.SetEventType(EVT_RESULT_ID)
		self.response = response

class ExceptionEvent(wx.PyEvent):
	"""Simple event to carry arbitrary result data."""

	def __init__(self, response):
		wx.PyEvent.__init__(self)
		self.SetEventType(EVT_EXCEPTION_ID)
		self.response = response

# Thread class that executes processing
class WorkerThread(Thread):
	def __init__(self, notify_window, func):
		Thread.__init__(self)
		self._notify_window = notify_window
		self._want_abort = 0
		self.setDaemon(1)
		self._func = func
		# This starts the thread running on creation, but you could
		# also make the GUI thread responsible for calling this
		self.start()

	def setFunc(self, func):
		self._func = func

	def run(self):
		try:
			response = self._func()
			# Done, send notify:
			wx.PostEvent(self._notify_window,ResultEvent(response))
		except Exception, e:
			wx.PostEvent(self._notify_window,ExceptionEvent(e))


# Timer that controls display of the dialog
class dProgressTimer(wx.Timer):
	def __init__(self, parent, func, wait=1):
		self.parent = parent
		self.dlg = None
		wx.Timer.__init__(self)
#		self.Start(1000 * wait, True)
		func()
		self.Stop()
		if self.dlg is not None:
			self.dlg.Destroy()


	def Notify(self):
		self.dlg = dProgressDialog(self.parent, caption="Running...")
		self.dlg.Show(True)


# GUI Frame class that spins off the worker thread
class dProgressDialog(wx.Dialog):
	def __init__(self, parent, caption="Progress Dialog"):
		wx.Dialog.__init__(self,parent,-1,caption)
		self.Centre(wx.BOTH)
		self.SetSize((300,100))
		self.status = wx.StaticText(self,-1,'Please Wait...',pos=(0,100))


def displayAfterWait(parentWindow, seconds, func):
	# Start <func>, but if it hasn't finished in <seconds>, display a
	# 'please wait' dialog box.

	tm = dProgressTimer(parentWindow, func, seconds)
# 	window = dProgressDialog(parentWindow, "Please Wait...", func, seconds)
# 	window.ShowModal()
# 	response = window.response
# 	window.Destroy()
# 	return response
