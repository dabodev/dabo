""" dControlMixin.py: Provide behavior common to all dControls """

import wx
import dPemMixin as pm

class dControlMixin(pm.dPemMixin):
	""" Provide common functionality for all controls.
	"""
	def __init__(self, name=None):
		pm.dPemMixin.__init__(self)

		self.debug = False
		
		if not name:
			name = self.Name
		
		try:
			self.Name = name		
		except NameError:
			# Name isn't unique: add an incrementing integer at the end and loop until
			# a unique name is found.
			nameNum = 1
			while True:
				try:				
					self.Name = "%s%s" % (name, nameNum)
					break
				except NameError:
					nameNum += 1

		self.Caption = self.getDefaultText()

		# Subclass will intercept the initEvents first, allowing
		# the framework user to completely override if desired.    
		self.initEvents()

		self._dForm = None
		self.addToDform()


	def getDform(self):
		""" Return a reference to the containing dForm. 
		"""
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
		""" Ask the dForm to add this control to its registry.
		"""
		try:
			self.getDform().addControl(self)
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
			print "OnSetFocus received by %s" % self.GetName()
		event.Skip()


	def OnKillFocus(self, event):
		""" Occurs when the control loses the keyboard focus.
		"""
		if self.debug:
			print "OnKillWindow received by %s" % self.GetName()
		event.Skip()


	def OnEnterWindow(self, event):
		""" Occurs when the mouse pointer enters the bounds of the control.
		"""
		if self.debug:
			print "OnEnterWindow received by %s" % self.GetName()
		event.Skip()


	def OnLeaveWindow(self, event):
		""" Occurs when the mouse pointer exits the bounds of the control.
		"""
		if self.debug:
			print "OnLeaveWindow received by %s" % self.GetName()
		event.Skip()


