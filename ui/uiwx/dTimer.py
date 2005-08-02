import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dabo.dEvents as dEvents
from dabo.dLocalize import _
import dIcons

class dTimer(dabo.ui.dBitmap):
	""" Create a timer. 
	"""
	_IsContainer = False
	
	# Note: this class is implemented as a static bitmap which serves as
	# a proxy to the underlying timer object. This was to allow the timer
	# to have a parent object and to fit in with the dabo events. This will
	# also allow the timer to have visual representation in the designer
	# (but we need to design a bitmap) while being invisible at runtime.
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		super(dTimer, self).__init__(parent=parent, properties=properties, *args, **kwargs)
		self._baseClass = dTimer

		
	def _afterInit(self):
		self.Picture = "dTimer"
		self._timer = wx.Timer(self)
		super(dTimer, self)._afterInit()
		self.Visible = False
	
		
	def _initEvents(self):
		super(dTimer, self)._initEvents()
		self.Bind(wx.EVT_TIMER, self._onWxHit)
		
		
	def isRunning(self):
		return self._timer.IsRunning()
		
		
	def Show(self, *args, **kwargs):
		# only let the the bitmap be shown if this is design time
		designTime = (self.Application is None)
		if designTime:
			#dTimer.doDefault(*args, **kwargs)
			super(dTimer, self).Show(*args, **kwargs)
		else:
			self.Bitmap = None
			
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
		if self._constructed():
			if val:
				self.Enable()
			else:
				self.Disable()
		else:
			self._properties["Enabled"] = val
		
	Interval = property(_getInterval, _setInterval, None,
		 _("Specifies the timer interval (milliseconds)."))
	
	Enabled = property(_getEnabled, _setEnabled, None,
			_("Alternative means of starting/stopping the timer, or determining "
			"its status. If Enabled is set to True and the timer has a positive value "
			"for its Interval, the timer will be started."))
	
	
if __name__ == "__main__":
	import test
	
	class C(dTimer):
		def afterInit(self):
			self.Interval = 1000
			self.start()
		def initEvents(self):
			self.bindEvent(dabo.dEvents.Hit, self.onHit)
		def onHit(self, evt):
			print "timer fired!"
		
	test.Test().runTest(C)
