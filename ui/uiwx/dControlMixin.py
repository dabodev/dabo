""" dControlMixin.py: Provide behavior common to all dControls """

import dabo
import dPemMixin as pm
from dabo.dLocalize import _
import dEvents

class dControlMixin(pm.dPemMixin):
	""" Provide common functionality for all controls.
	"""
	def __init__(self, name=None):
		pm.dPemMixin.__init__(self)

		self.debug = False
		
		if not name:
			name = self.Name
		
		self.Name = name		

		# Subclass will intercept the initEvents first, allowing
		# the framework user to completely override if desired.    
		self.initEvents()
		self.addToDform()

	def initEvents(self):
		pass
		
	def addToDform(self):
		""" Ask the dForm to add this control to its registry.
		"""
		try:
			self.Form.addControl(self)
		except AttributeError:
			# perhaps the form isn't a dForm
			pass


	def onCreate(self, event):
		""" Occurs after the init phase is complete.
		"""
		if self.debug:
			dabo.infoLog.write(_("onCreate received by %s") % self.Name)
		event.Skip()
		
	
	def onDestroy(self, event):
		""" Occurs during the destroy phase.
		
		It is possible that not all attributes of the object will still
		be available on all platforms.
		"""
		if self.debug:
			dabo.infoLog.write(_("onDestroy received by %s") % self.Name)
		event.Skip()
		
		
	def onGotFocus(self, event):
		""" Occurs when the control receives the keyboard focus.
		"""
		if self.debug:
			dabo.infoLog.write(_("onGotFocus received by %s") % self.Name)
		event.Skip()


	def onLostFocus(self, event):
		""" Occurs when the control loses the keyboard focus.
		"""
		if self.debug:
			dabo.infoLog.write(_("onLostFocus received by %s") % self.Name)
		event.Skip()


	def onMouseEnter(self, event):
		""" Occurs when the mouse pointer enters the bounds of the control.
		"""
		if self.debug:
			dabo.infoLog.write(_("onMouseEnter received by %s") % self.Name)
		event.Skip()


	def onMouseLeave(self, event):
		""" Occurs when the mouse pointer exits the bounds of the control.
		"""
		if self.debug:
			dabo.infoLog.write(_("onMouseLeave received by %s") % self.Name)
		event.Skip()

		
	def onMouseLeftClick(self, event):
		if self.debug:
			dabo.infoLog.write(_("onMouseLeftClick received by %s") % self.Name)
		event.Skip()
		
		
	def onMouseRightClick(self, event):
		if self.debug:
			dabo.infoLog.write(_("onMouseRightClick received by %s") % self.Name)
		event.Skip()

		
	def onMouseLeftDoubleClick(self, event):
		if self.debug:
			dabo.infoLog.write(_("onMouseLeftDoubleClick received by %s") % self.Name)
		event.Skip()

	def onKeyChar(self, event):
		if self.debug:
			dabo.infoLog.write(_("onKeyChar received by %s. Key: %s") % (self.Name, chr(event.KeyCode())))
		event.Skip()
		
	def onKeyDown(self, event):
		if self.debug:
			dabo.infoLog.write(_("onKeyDown received by %s. KeyCode: %s") % (self.Name, event.KeyCode()))
		event.Skip()