import wx
import dControlMixin, dEvents
from dabo.dLocalize import _

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
		wx.StaticBitmap.__init__(self, parent, name=name, *args, **kwargs)
		
		self.Hide()
		
		self._timer = wx.Timer(self)

		dControlMixin.dControlMixin.__init__(self, name)
		
		self._afterInit()
		
		self.bindEvent(dEvents.Timer, self._onTimer)
		self.bindEvent(dEvents.Timer, self.onTimer)
		
				
	def beforeInit(self, pre): pass
	def afterInit(self): pass

	def start(self):
		self._timer.Start()
		
	def stop(self):
		self._timer.Stop()
			
	def onTimer(self, event): pass
	
	def _onTimer(self, event): pass
	
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
		 _("Specifies the timer interval (milliseconds) and starts the timer."))
	
if __name__ == "__main__":
	import dabo.ui
	dabo.ui.loadUI('wx')
	
	class test(dTimer):
		def afterInit(self):
			self.count = 0
			self.Interval = 1000
			
		def onTimer(self, event):
			self.count += 1
			print "onTimer!!", event.GetEventObject()
			if self.count > 10:
				self.Interval = 0
			event.Skip()
	
	app = wx.PySimpleApp()
	form = dabo.ui.dForm()
	form.Show()
	t = test(form)
	app.MainLoop()