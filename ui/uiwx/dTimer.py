import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as dControlMixin
import dabo.dEvents as dEvents
from dabo.dLocalize import _
import dIcons

class dTimer(wx.StaticBitmap, dControlMixin.dControlMixin):
	""" Create a timer. 
	"""
	
	# Note: this class is implemented as a static bitmap which serves as
	# a proxy to the underlying timer object. This was to allow the timer
	# to have a parent object and to fit in with the dabo events. This will
	# also allow the timer to have visual representation in the designer
	# (but we need to design a bitmap) while being invisible at runtime.
	
	def __init__(self, parent, *args, **kwargs):
		self._baseClass = dTimer
		name, _explicitName = self._processName(kwargs, "dTimer")

		self._beforeInit(None)
		# no 2-stage creation for Timers
		
		# Get a timer bitmap, but for now use the dabo icon:
		bitmap = dIcons.getIconBitmap("dTimer", setMask=False)
		wx.StaticBitmap.__init__(self, parent, bitmap=bitmap, *args, **kwargs)
		
		self.Hide()
		self._timer = wx.Timer(self)
		self._interval = 0

		dControlMixin.dControlMixin.__init__(self, name, _explicitName=_explicitName)
		
		self._afterInit()
		
		
	def initEvents(self):
		#dTimer.doDefault()
		super(dTimer, self).initEvents()
		self.Bind(wx.EVT_TIMER, self._onWxHit)
	
	def isRunning(self):
		return self._timer.IsRunning()
		
	def Show(self, *args, **kwargs):
		# only let the the bitmap be shown if this is design time
		designTime = (self.Application is None)
		if designTime:
			#dTimer.doDefault(*args, **kwargs)
			super(dTimer, self).Show(*args, **kwargs)
	
	def start(self, interval=-1):
		if interval >= 0:
			self._interval = interval
		if self._interval > 0:
			self._timer.Start(self._interval)
		else:
			self._timer.Stop()
		return self._timer.IsRunning()
	
	def stop(self):
		self._timer.Stop()
		return not self._timer.IsRunning()
		
	# property get/set functions
	def _getInterval(self):
		return self._interval
	
	def _setInterval(self, val):
		self._interval = val
	
	def _getEnabled(self):
		return self._timer.IsRunning()
		
	def _setEnabled(self, val):
		if val:
			self.Enable()
		else:
			self.Disable()

		
	Interval = property(_getInterval, _setInterval, None,
		 _("Specifies the timer interval (milliseconds)."))
	
	Enabled = property(_getEnabled, _setEnabled, None,
			_("Alternative means of starting/stopping the timer, or determining "
			"its status. If Enabled is set to True and the timer has a positive value "
			"for its Interval, the timer will be started."))
	
	
if __name__ == "__main__":
	import test
	
	class c(dTimer):
		def afterInit(self):
			self.Interval = 1000
	test.Test().runTest(c)
