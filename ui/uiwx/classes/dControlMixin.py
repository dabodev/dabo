''' dControlMixin.py: Provide behavior common to all dControls '''

import wx
import dPemMixin as pm

class dControlMixin(pm.dPemMixin):
	''' Provide common functionality for all controls.
	'''
	def __init__(self, name=None):
		pm.dPemMixin.__init__(self)

		self.debug = False
		if name:
			self.Name = name
		self.Caption = self.getDefaultText()

		# Subclass will intercept the initEvents first, allowing
		# the framework user to completely override if desired.    
		self.initEvents()

		self._dForm = None
		self.addToDform()


	def getDform(self):
		''' Return a reference to the containing dForm. 
		'''
		if self._dForm:
			return self._dForm      # Already cached
		else:
			import dForm
			obj, frm = self, None
			while obj:
				parent = obj.GetParent()
				if isinstance(parent, dForm.dForm):
					frm = parent
					break
				else:
					obj = parent
			if frm:
				self._dForm = frm   # Cache for next time
			return frm


	def addToDform(self):
		''' Ask the dForm to add this control to its registry.
		'''
		try:
			self.getDform().addControl(self)
		except AttributeError:
			# perhaps the form isn't a dForm
			pass


	def getDefaultText(self):
		''' Get default text to describe this object.
		'''
		return "Dabo: %s" % self.GetName()


	def initEvents(self):
		''' Initialize common event callbacks.
		'''
		wx.EVT_ENTER_WINDOW(self, self.OnEnterWindow) 
		wx.EVT_LEAVE_WINDOW(self, self.OnLeaveWindow) 
		wx.EVT_SET_FOCUS(self, self.OnSetFocus)
		wx.EVT_KILL_FOCUS(self, self.OnKillFocus)


	def OnSetFocus(self, event):
		''' Occurs when the control receives the keyboard focus.
		'''
		if self.debug:
			print "OnSetFocus received by %s" % self.GetName()
		event.Skip()


	def OnKillFocus(self, event):
		''' Occurs when the control loses the keyboard focus.
		'''
		if self.debug:
			print "OnKillWindow received by %s" % self.GetName()
		event.Skip()


	def OnEnterWindow(self, event):
		''' Occurs when the mouse pointer enters the bounds of the control.
		'''
		if self.debug:
			print "OnEnterWindow received by %s" % self.GetName()
		event.Skip()


	def OnLeaveWindow(self, event):
		''' Occurs when the mouse pointer exits the bounds of the control.
		'''
		if self.debug:
			print "OnLeaveWindow received by %s" % self.GetName()
		event.Skip()


