# -*- coding: utf-8 -*-
import dabo
from dabo.ui import makeDynamicProperty
if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dPemMixin import dPemMixin as PM
import dPanel


class dTimer(PM):
	"""Creates a timer, for causing something to happen at regular intervals."""
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dTimer
		super(dTimer, self).__init__(preClass=None, parent=parent, properties=properties, *args, **kwargs)


	def isRunning(self):
		return self.Enabled


	def start(self, interval=-1):
		if interval >= 0:
			self.Interval = interval
		self.Enabled = self.Interval > 0
		return self.Enabled


	def stop(self):
		self.Enabled = False


	def release(self):
		"""Make sure that the timer is stopped first"""
		self.stop()
		super(dTimer, self).release()


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
	def Bind(self, *args, **kwargs):
		pass
	def Destroy(self):
		pass


	def _onTimerHit(self):
		if self.Enabled and self.Interval > 0:
			self.raiseEvent(dEvents.Hit)
			dabo.ui.callAfterInterval(self.Interval, self._onTimerHit)


	# property get/set functions
	def _getEnabled(self):
		return getattr(self, "_enabled", False)

	def _setEnabled(self, val):
		self._enabled = val
		if val:
			dabo.ui.callAfterInterval(self.Interval, self._onTimerHit)
		else:
			self._properties["Enabled"] = val


	def _getInterval(self):
		try:
			v = self._interval
		except AttributeError:
			v = self._interval = 0
		return v

	def _setInterval(self, val):
		self._interval = val


	Enabled = property(_getEnabled, _setEnabled, None,
			_("""Alternative means of starting/stopping the timer, or determining
			its status. If Enabled is set to True and the timer has a positive value
			for its Interval, the timer will be started.  (bool)"""))

	Interval = property(_getInterval, _setInterval, None,
			_("Specifies the timer interval (milliseconds)."))


	DynamicEnabled = makeDynamicProperty(Enabled)
	DynamicInterval = makeDynamicProperty(Interval)


class _dTimer_test(dPanel.dPanel):
	def afterInit(self):
		# Only setting this so that the test Caption is correct
		self._baseClass = dTimer
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
