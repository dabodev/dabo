from dabo.ui.dControlMixinBase import dControlMixinBase
import dabo.dEvents as dEvents

class dControlMixin(dControlMixinBase):
	
	def _onTkHit(self, event):
		self.raiseEvent(dEvents.Hit, event)
		
