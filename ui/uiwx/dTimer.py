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
	
	def __init__(self, parent, name='dTimer', *args, **kwargs):

		self._baseClass = dTimer

		self._beforeInit(None)
		# no 2-stage creation for Timers
		
		# Get a timer bitmap, but for now use the dabo icon:
		bitmap = dIcons.getIconBitmap("dTimer", setMask=False)
		wx.StaticBitmap.__init__(self, parent, name=name, bitmap=bitmap, *args, **kwargs)
		
		self.Hide()
		self._timer = wx.Timer(self)

		dControlMixin.dControlMixin.__init__(self, name)
		
		self._afterInit()
		
	def initEvents(self):
		dTimer.doDefault()
		self.Bind(wx.EVT_TIMER, self._onWxHit)
		
	def Show(self, *args, **kwargs):
		# only let the the bitmap be shown if this is design time
		designTime = (self.Application is None)
		if designTime:
			dTimer.doDefault(*args, **kwargs)
		
		
	# property get/set functions
	def _getInterval(self):
		if self._timer.IsRunning():
			return self._timer.GetInterval()
		else:
			return 0
	
	def _setInterval(self, val):
		if val <= 0:
			self._timer.Stop()
		else:
			self._timer.Start(val)

		
	Interval = property(_getInterval, _setInterval, None,
		 _("Specifies the timer interval (milliseconds) and starts the timer. Set to 0 "
		 "to stop the timer."))
	
if __name__ == "__main__":
	import test
	
	class c(dTimer):
		def afterInit(self):
			self.Interval = 1000
	test.Test().runTest(c)
