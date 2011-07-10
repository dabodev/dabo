# -*- coding: utf-8 -*-
import time
import wx
import dabo.ui
from dabo.ui.dControlMixinBase import dControlMixinBase
from dabo.dLocalize import _
import dabo.dEvents as dEvents


class dControlMixin(dControlMixinBase):
	def _initEvents(self):
		super(dControlMixin, self)._initEvents()
		self.Bind(wx.EVT_NAVIGATION_KEY, self.__onWxNavKey)

	def _onWxHit(self, evt, *args, **kwargs):
		# This is called by a good number of the controls, when the default
		# event happens, such as a click in a command button, text being
		# entered in a text control, a timer reaching its interval, etc.
		# We catch the wx event, and raise the dabo Hit event for user code
		# to work with.

		# Hide a problem on Windows toolbars where a single command event will
		# be raised up to three separate times.
# 		print "CONTROL WXHIT", self, evt
		now = time.time()
		if not hasattr(self, "_lastHitTime") or (now - self._lastHitTime) > .001:
			self.raiseEvent(dEvents.Hit, evt, *args, **kwargs)
#			print "CONTROL RAISING HIT"
			self._lastHitTime = time.time()

	def __onWxNavKey(self, evt):
		# A navigation key event has caused this control to want to
		# get the focus. Only allow it if self.TabStop is True.
		evt.Skip()
		if not self.TabStop:
			dabo.ui.callAfter(self.Navigate, evt.GetDirection())


	def _getTabStop(self):
		return getattr(self, "_tabStop", True)

	def _setTabStop(self, val):
		assert isinstance(val, bool)
		self._tabStop = val


	TabStop = property(_getTabStop, _setTabStop, None,
			_("Specifies whether this control can receive focus from keyboard navigation."))
