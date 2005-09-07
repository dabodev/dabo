""" dPemMixin.py: Provide common PEM functionality """
import dabo, dabo.common
import types
from dabo.dLocalize import _

class dPemMixinBase(dabo.common.dObject):
	""" Provide Property/Event/Method interfaces for dForms and dControls.

	Subclasses can extend the property sheet by defining their own get/set
	functions along with their own property() statements.
	"""
	
	_call_beforeInit, _call_afterInit = False, False

	def _initUI(self):
		""" Abstract method: subclasses MUST override for UI-specifics.
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
		pass


	def _initName(self, name=None, _explicitName=True):
		if name is None:
			name = self.Name
		try:
			self._setName(name, _userExplicit=_explicitName)
		except AttributeError:
			# Some toolkits (Tkinter) don't let objects change their
			# names after instantiation.
			pass

			
	def _processName(self, kwargs, defaultName):
		# Called by the constructors of the dObjects, to properly set the
		# name of the object based on whether the user set it explicitly
		# or Dabo is to provide it implicitly.
		if "Name" in kwargs.keys():
			if "_explicitName" in kwargs.keys():
				_explicitName = kwargs["_explicitName"]
				del kwargs["_explicitName"]
			else:
				_explicitName = True
			name = kwargs["Name"]
		else:
			_explicitName = False
			name = defaultName
		return name, _explicitName
		


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
				try:
					parent = obj.Parent
				except AttributeError:
					break
				if isinstance(parent, (dabo.ui.dForm, dabo.ui.dFormMain, 
				                       dabo.ui.dDialog) ):
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
