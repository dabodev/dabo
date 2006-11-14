import wx
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dabo.dEvents as dEvents
from dabo.dLocalize import _
import dControlMixin as cm
from dabo.ui import makeDynamicProperty
import dPanel


class dTimer(wx.Timer, cm.dControlMixin):
	"""Creates a timer, for causing something to happen at regular intervals."""
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dTimer
		preClass = wx.Timer
		cm.dControlMixin.__init__(self, preClass, parent=None, 
				properties=properties, *args, **kwargs)

		if parent is not None:
			self.SetOwner(parent)
			parent.Bind(wx.EVT_TIMER, self._onWxHit)
		else:
			self.Bind(wx.EVT_TIMER, self._onWxHit)
		
		
	def isRunning(self):
		return self.IsRunning()
		

	def start(self, interval=-1):
		if interval >= 0:
			self.Interval = interval
		if self.Interval > 0:
			self.Start(self.Interval)
		else:
			self.Stop()
		return self.IsRunning()
	
		
	def stop(self):
		self.Stop()
		return not self.IsRunning()
	
	
	# The following methods are not needed except for 
	# compatibility with the various properties.
	def Show(self, val):
		pass
	def GetSize(self):
		return (-1, -1)
	def SetBestFittingSize(self, val):
		pass
	def GetParent(self):
		return None
		
		
	# property get/set functions
	def _getInterval(self):
		try:
			v = self._interval
		except AttributeError:
			v = self._interval = 0
		return v
	
	def _setInterval(self, val):
		self._interval = val
	
	
	def _getEnabled(self):
		return self.IsRunning()
		
	def _setEnabled(self, val):
		if self._constructed():
			if val:
				self.start()
			else:
				self.stop()
		else:
			self._properties["Enabled"] = val
			
		
	Interval = property(_getInterval, _setInterval, None,
			_("Specifies the timer interval (milliseconds)."))
	DynamicInterval = makeDynamicProperty(Interval)
	
	Enabled = property(_getEnabled, _setEnabled, None,
			_("Alternative means of starting/stopping the timer, or determining "
			"its status. If Enabled is set to True and the timer has a positive value "
			"for its Interval, the timer will be started."))
	DynamicEnabled = makeDynamicProperty(Enabled)
	
	
class _dTimer_test(dPanel.dPanel):
	def afterInit(self):
		self.fastTimer = dTimer(self, Interval=500)
		self.fastTimer.bindEvent(dEvents.Hit, self.onFastTimerHit)
		self.slowTimer = dTimer(Interval=2000)
		self.slowTimer.bindEvent(dEvents.Hit, self.onSlowTimerHit)
		self.fastTimer.start()
		self.slowTimer.start()

	def onFastTimerHit(self, evt):
		print "fast timer fired!"
		
	def onSlowTimerHit(self, evt):
		print "slow timer fired!"
		

if __name__ == "__main__":
	import test
	test.Test().runTest(_dTimer_test)
