# -*- coding: utf-8 -*-
from dabo.ui.dControlMixinBase import dControlMixinBase
from dabo import dEvents as dEvents

class dControlMixin(dControlMixinBase):

	def _onTkHit(self, evt):
		self.raiseEvent(dEvents.Hit, evt)

