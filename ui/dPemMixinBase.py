""" dPemMixin.py: Provide common PEM functionality """
import dabo, dabo.common
import types
from dabo.dLocalize import _

class dPemMixinBase(dabo.common.dObject):
	""" Provide Property/Event/Method interfaces for dForms and dControls.

	Subclasses can extend the property sheet by defining their own get/set
	functions along with their own property() statements.
	"""
	
	def __getattr__(self, att):
		""" Abstract method: subclasses MUST override for UI-specifics.
		"""
		pass
	
	def _beforeInit(self):
		""" Abstract method: subclasses MUST override for UI-specifics.
		"""
		pass
		
	def _afterInit(self):
		""" Abstract method: subclasses MUST override for UI-specifics.
		"""
		pass
	
	def beforeInit(self, *args, **kwargs):
		""" Subclass hook.
		
		Called before the object is fully instantiated.
		"""
		pass
		

	def afterInit(self):
		""" Subclass hook.
		
		Called after the object's __init__ has run fully.

		Subclasses should place their __init__ code here in this hook,
		instead of overriding __init__ directly, to avoid conflicting
		with base Dabo behavior.
		"""
		pass
		

	def initProperties(self):
		""" Hook for subclasses.

		User code can set properties here, such as:
			self.Name = "MyTextBox"
			self.BackColor = (192,192,192)
		"""
		pass

		
	def initEvents(self):
		""" Hook for subclasses.
		
		User code can do custom event binding here, such as:
			self.bindEvent(dEvents.GotFocus, self.customGotFocusHandler)
		"""
		pass
		
			
	def initStyleProperties(self):
		""" Hook for subclasses.

		User code can set style properties here, such as:
			self.BorderStyle = "Sunken"
			self.Alignment = "Center"
		"""
		pass

		
	def initChildObjects(self):
		""" Hook for subclasses.
		
		Dabo Designer will set its addObject code here, such as:
			self.addObject(dTextBox, 'txtLastName')
		"""
		pass
		

	def getPropertyInfo(self, name):
		""" Abstract method: subclasses MUST override for UI-specifics.
		"""
		return super(dPemMixinBase, self).getPropertyInfo(name)
		
	
	def addObject(self, classRef, name=None, *args, **kwargs):
		""" Create an instance of classRef, and make it a child of self.
		
		Abstract method: subclasses MUST override for UI-specifics.
		"""
		pass
		

	def reCreate(self, child=None):
		""" Abstract method: subclasses MUST override for UI-specifics.
		"""
	
	def clone(self, obj, name=None):
		""" Abstract method: subclasses MUST override for UI-specifics.
		"""
		

	# Scroll to the bottom to see the property definitions.

	# Property get/set/delete methods follow.
	
		
	def _getForm(self):
		""" Return a reference to the containing Form. 
		"""
		try:
			return self._cachedForm
		except AttributeError:
			import dabo.ui
			obj, frm = self, None
			while obj:
				parent = obj.Parent
				if isinstance(parent, dabo.ui.dForm):
					frm = parent
					break
				else:
					obj = parent
			if frm:
				self._cachedForm = frm   # Cache for next time
			return frm


	def _getBottom(self):
		return self.Top + self.Height
	def _setBottom(self, bottom):
		self.Top = int(bottom) - self.Height

	def _getRight(self):
		return self.Left + self.Width
	def _setRight(self, right):
		self.Left = int(right) - self.Width




	# Property definitions follow
	Bottom = property(_getBottom, _setBottom, None,
					'The position of the bottom part of the object. (int)')
	
	Form = property(_getForm, None, None,
					'Object reference to the dForm containing the object. (read only).')
	
	Right = property(_getRight, _setRight, None,
					'The position of the right part of the object. (int)')


if __name__ == "__main__":
	o = dPemMixin()
	print o.BaseClass
	o.BaseClass = "dForm"
	print o.BaseClass
