from dabo.ui.dControlMixinBase import dControlMixinBase
import dabo.dEvents as dEvents

class dControlMixin(dControlMixinBase):
	
	def _onWxHit(self, evt):
		self.raiseEvent(dEvents.Hit, evt)
		evt.Skip()
		
