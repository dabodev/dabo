# -*- coding: utf-8 -*-
from dabo.ui.dControlMixinBase import dControlMixinBase
import dabo.dEvents as dEvents

class dControlMixin(dControlMixinBase):

	def _onTkHit(self, evt):
		self.raiseEvent(dEvents.Hit, evt)

