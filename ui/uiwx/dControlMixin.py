""" dControlMixin.py: Provide behavior common to all dControls """

import wx
import dabo
import dPemMixin as pm
from dabo.dLocalize import _

class dControlMixin(pm.dPemMixin):
	""" Provide common functionality for all controls.
	"""
	def __init__(self, name=None):
		pm.dPemMixin.__init__(self)

		self.debug = False
		
		if not name:
			name = self.Name
		
		self.Name = name		
		#self.Caption = self.getDefaultText()

		# Subclass will intercept the initEvents first, allowing
		# the framework user to completely override if desired.    
		self.initEvents()
		self.addToDform()


	def addToDform(self):
		""" Ask the dForm to add this control to its registry.
		"""
		try:
			self.Form.addControl(self)
		except AttributeError:
			# perhaps the form isn't a dForm
			pass


	def getDefaultText(self):
		""" Get default text to describe this object.
		"""
		return "Dabo: %s" % self.GetName()


	def initEvents(self):
		""" Initialize common event callbacks.
		"""
		self.Bind(wx.EVT_WINDOW_CREATE, self.OnCreateWindow)
		self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroyWindow)
		self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterWindow) 
		self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWindow) 
		self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
		self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)


	def OnCreateWindow(self, event):
		""" Occurs after the init phase is complete.
		"""
		pass
		
	
	def OnDestroyWindow(self, event):
		""" Occurs during the destroy phase.
		
		It is possible that not all attributes of the object will still
		be available on all platforms.
		"""
		pass
		
		
	def OnSetFocus(self, event):
		""" Occurs when the control receives the keyboard focus.
		"""
		if self.debug:
			dabo.infoLog.write(_("OnSetFocus received by %s") % self.GetName())
		event.Skip()


	def OnKillFocus(self, event):
		""" Occurs when the control loses the keyboard focus.
		"""
		if self.debug:
			dabo.infoLog.write(_("OnKillWindow received by %s") % self.GetName())
		event.Skip()


	def OnEnterWindow(self, event):
		""" Occurs when the mouse pointer enters the bounds of the control.
		"""
		if self.debug:
			dabo.infoLog.write(_("OnEnterWindow received by %s") % self.GetName())
		event.Skip()


	def OnLeaveWindow(self, event):
		""" Occurs when the mouse pointer exits the bounds of the control.
		"""
		if self.debug:
			dabo.infoLog.write(_("OnLeaveWindow received by %s") % self.GetName())
		event.Skip()


