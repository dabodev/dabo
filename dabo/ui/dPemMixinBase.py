# -*- coding: utf-8 -*-
"""dPemMixin.py: Provide common PEM functionality"""
import dabo
import types
from dabo.dObject import dObject
import dabo.dException as dException
from dabo.dLocalize import _


class dPemMixinBase(dObject):
	"""
	Provide Property/Event/Method interfaces for dForms and dControls.

	Subclasses can extend the property sheet by defining their own get/set
	functions along with their own property() statements.
	"""
	def _initEvents(self):
		super(dPemMixinBase, self)._initEvents()
		self.autoBindEvents()

	def _initUI(self):
		"""Abstract method: subclasses MUST override for UI-specifics."""
		pass


	def getPropertyInfo(cls, name):
		"""Abstract method: subclasses MUST override for UI-specifics."""
		return super(dPemMixinBase, cls).getPropertyInfo(name)
	getPropertyInfo = classmethod(getPropertyInfo)


	def addObject(self, classRef, Name=None, *args, **kwargs):
		"""
		Create an instance of classRef, and make it a child of self.

		Abstract method: subclasses MUST override for UI-specifics.
		"""
		pass


	def reCreate(self, child=None):
		"""Abstract method: subclasses MUST override for UI-specifics."""
		pass


	def clone(self, obj, name=None):
		"""Abstract method: subclasses MUST override for UI-specifics."""
		pass

	def refresh(self):
		"""Abstract method."""
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
		_explicitName = kwargs.get("_explicitName", False)

		if "Name" in kwargs:
			if "_explicitName" not in kwargs:
				# Name was sent; _explicitName wasn't.
				_explicitName = True
			name = kwargs["Name"]
		else:
			name = defaultName

		if "_explicitName" in kwargs:
			del(kwargs["_explicitName"])
		return name, _explicitName


	def iterateCall(self, funcName, *args, **kwargs):
		"""
		Call the given function on this object and all of its Children. If
		any object does not have the given function, no error is raised; it
		is simply ignored.
		"""
		func = getattr(self, funcName, None)
		if func:
			try:
				func(*args, **kwargs)
			except dException.StopIterationException:
				# This is raised when the object does not want to pass
				# the iteration on through its Children.
				func = None
		if func:
			for child in self.Children:
				if hasattr(child, "iterateCall"):
					child.iterateCall(funcName, *args, **kwargs)


	# These five functions are essentially a single unit that provides font zooming.
	def fontZoomIn(self, amt=1):
		"""Zoom in on the font, by setting a higher point size."""
		self._setRelativeFontZoom(amt)

	def fontZoomOut(self, amt=1):
		"""Zoom out on the font, by setting a lower point size."""
		self._setRelativeFontZoom(-amt)

	def fontZoomNormal(self):
		"""Reset the font zoom back to zero."""
		self._setAbsoluteFontZoom(0)

	def _setRelativeFontZoom(self, amt):
		abs_zoom = getattr(self, "_currFontZoom", 0) + amt
		self._setAbsoluteFontZoom(abs_zoom)

	def _setAbsoluteFontZoom(self, newZoom):
		if not hasattr(self, "FontSize"):
			# Menus, for instance
			return
		origFontSize = getattr(self, "_origFontSize", None)
		if origFontSize is None:
			self._origFontSize = self.FontSize
			fontSize = self.FontSize + newZoom
		else:
			fontSize = origFontSize + newZoom
		self._currFontZoom = newZoom
		if fontSize > 1:
			self.FontSize = fontSize
		dabo.ui.callAfterInterval(200, self.refresh)

		if isinstance(self, dabo.ui.dFormMixin):
			frm = self
		else:
			frm = self.Form
		if frm is not None:
			dabo.ui.callAfterInterval(200, frm.layout)

	def _restoreFontZoom(self):
		"""Called when object is instantiated: restore the zoom based on the form."""
		if not hasattr(self.Form, "_currFontZoom"):
			self.Form._restoreFontZoom()
		zoom = getattr(self.Form, "_currFontZoom", 0)
		if zoom and not isinstance(self, (dabo.ui.dPanel, dabo.ui.dScrollPanel)):
			dabo.ui.callAfter(self._setAbsoluteFontZoom, zoom)


	# Property get/set/delete methods follow.
	def _getChildren(self):
		return []

	def _getForm(self):
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
				if isinstance(parent, (dabo.ui.dFormMixin)):
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
		if self._constructed():
			self.Top = int(bottom) - self.Height
		else:
			self._properties["Bottom"] = bottom


	def _getRight(self):
		return self.Left + self.Width

	def _setRight(self, right):
		if self._constructed():
			self.Left = int(right) - self.Width
		else:
			self._properties["Right"] = right


	Bottom = property(_getBottom, _setBottom, None,
			_("""The position of the bottom side of the object. This is a
			convenience property, and is equivalent to setting the Top property
			to this value minus the Height of the control.  (int)"""))

	Children = property(_getChildren, None, None,
			_("""List of child objects."""))

	Form = property(_getForm, None, None,
			_("Object reference to the dForm containing the object. Read-only. (dForm)."))

	Right = property(_getRight, _setRight, None,
			_("""The position of the right side of the object. This is a
			convenience property, and is equivalent to setting the Left property
			to this value minus the Width of the control.  (int)"""))



if __name__ == "__main__":
	o = dPemMixin()
	print o.BaseClass
	o.BaseClass = "dForm"
	print o.BaseClass
