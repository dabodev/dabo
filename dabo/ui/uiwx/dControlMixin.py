# -*- coding: utf-8 -*-
import time
import wx
import dabo.ui
from dabo.ui.dControlMixinBase import dControlMixinBase
import dabo.dEvents as dEvents


class dControlMixin(dControlMixinBase):
	def _onWxHit(self, evt, *args, **kwargs):
		# This is called by a good number of the controls, when the default
		# event happens, such as a click in a command button, text being 
		# entered in a text control, a timer reaching its interval, etc.
		# We catch the wx event, and raise the dabo Hit event for user code
		# to work with.

		# Hide a problem on Windows toolbars where a single command event will
		# be raised up to three separate times.
		now = time.time()
		if not hasattr(self, "_lastHitTime") or (now - self._lastHitTime) > .001:
			self.raiseEvent(dEvents.Hit, evt, *args, **kwargs)
			self._lastHitTime = time.time()
		
