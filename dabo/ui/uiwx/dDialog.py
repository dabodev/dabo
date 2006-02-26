import wx
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
import dabo.dConstants as kons
from dabo.dLocalize import _
import dFormMixin as fm
from dabo.ui import makeDynamicProperty


class dDialog(wx.Dialog, fm.dFormMixin):
	"""Creates a dialog, which is a lightweight form.

	Dialogs are like forms, but typically are modal and are requesting a very
	specific piece of information from the user, and/or offering specific
	information to the user.
	"""
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dDialog
		self._modal = True
		self._centered = True
		self._fit = True

		defaultStyle = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
		try:
			kwargs["style"] = kwargs["style"] | defaultStyle
		except KeyError:
			kwargs["style"] = defaultStyle

		preClass = wx.PreDialog
		fm.dFormMixin.__init__(self, preClass, parent, properties=properties, 
				*args, **kwargs)

		# Hook method, so that we add the buttons last
		self._addControls()


	def _afterInit(self):
		self.MenuBarClass = None
		self.Sizer = dabo.ui.dSizer("V")
# 		self.mainPanel = mp = dabo.ui.dPanel(self)
# 		self.Sizer.append1x(mp)
# 		mp.Sizer = dabo.ui.dSizer("V")
		super(dDialog, self)._afterInit()
		self.bindKey("esc", self._onEscape)

		
	def show(self):
		if self.AutoSize:
			self.Fit()
		if self.Centered:
			wx.CallAfter(self.Centre)
		retVals = {wx.ID_OK : kons.DLG_OK, 
				wx.ID_CANCEL : kons.DLG_CANCEL}
		if self.Modal:
			ret = self.ShowModal()
		else:
			ret = self.Show(True)
		return retVals.get(ret)
		

	def _onEscape(self, evt):
		if self.ReleaseOnEscape:
			self.release()
			self.Close()


	def _addControls(self):
		"""Any controls that need to be added to the dialog 
		can be added in this method in framework classes, or
		in addControls() in instances.
		"""
		self.addControls()
	

	def addControls(self):
		"""Add your custom controls to the dialog.

		This is a hook, called at the appropriate time by the framework.
		"""
		pass


	def release(self):
		""" Need to augment this to make sure the dialog
		is removed from the app's forms collection.
		"""
		if self.Application is not None:
			try:
				self.Application.uiForms.remove(self)
			except: pass
		super(dDialog, self).release()
		

	def _getAutoSize(self):
		return self._fit

	def _setAutoSize(self, val):
		self._fit = val


	def _getCaption(self):
		return self.GetTitle()

	def _setCaption(self, val):
		if self._constructed():
			self.SetTitle(val)
		else:
			self._properties["Caption"] = val


	def _getCentered(self):
		return self._centered

	def _setCentered(self, val):
		self._centered = val


	def _getModal(self):
		return self._modal

	def _setModal(self, val):
		self._modal = val
	

	def _getReleaseOnEscape(self):
		try:
			val = self._releaseOnEscape
		except AttributeError:
			val = True
		return val

	def _setReleaseOnEscape(self, val):
		self._releaseOnEscape = bool(val)


	def _getShowStat(self):
		# Dialogs cannot have status bars.
		return False
	_showStatusBar	= property(_getShowStat)


	AutoSize = property(_getAutoSize, _setAutoSize, None,
			"When True, the dialog resizes to fit the added controls.  (bool)")
	DynamicAutoSize = makeDynamicProperty(AutoSize)

	Caption = property(_getCaption, _setCaption, None,
			"The text that appears in the dialog's title bar  (str)" )
	DynamicCaption = makeDynamicProperty(Caption)

	Centered = property(_getCentered, _setCentered, None,
			"Determines if the dialog is displayed centered on the screen.  (bool)")
	DynamicCentered = makeDynamicProperty(Centered)

	Modal = property(_getModal, _setModal, None,
			"Determines if the dialog is shown modal (default) or modeless.  (bool)")
	
	ReleaseOnEscape = property(_getReleaseOnEscape, _setReleaseOnEscape, None,
			"Determines if the <Esc> key releases the dialog (the default).")


class dOkCancelDialog(dDialog):
	"""Creates a dialog with OK/Cancel buttons and associated functionality.

	Add your custom controls in the addControls() hook method, and respond to
	the pressing of the Ok and Cancel buttons in the onOK() and onCancel() 
	event handlers. The default behavior in both cases is just to close the
	form, and you can query the Accepted property to find out if the user 
	pressed "OK" or not.
	"""
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dOkCancelDialog
		self._accepted = False
		super(dOkCancelDialog, self).__init__(parent=parent, properties=properties, *args, **kwargs)


	def _addControls(self):
		# Set some default Sizer properties (user can easily override):
		sz = self.Sizer
		sz.Border = 20
		sz.BorderLeft = sz.BorderRight = True
		sz.append((0, sz.Border))

		# Let the user add their controls
		super(dOkCancelDialog, self)._addControls()

		# Just in case user changed Self.Sizer, update our reference:
		sz = self.Sizer

		# Define Ok/Cancel, and tell wx that we want stock buttons:
		self.btnOK = dabo.ui.dButton(self, id=wx.ID_OK, DefaultButton=True)
		self.btnOK.bindEvent(dEvents.Hit, self.onOK)
		self.btnCancel = dabo.ui.dButton(self, id=wx.ID_CANCEL, CancelButton=True)
		self.btnCancel.bindEvent(dEvents.Hit, self.onCancel)
		
		# Put the buttons in a StdDialogButtonSizer, so they get positioned/sized
		# per the native platform conventions, and add that sizer to self.Sizer:
		buttonSizer = wx.StdDialogButtonSizer()
		buttonSizer.AddButton(self.btnOK)
		buttonSizer.AddButton(self.btnCancel)
		buttonSizer.Realize()

		# Wx rearranges the order of the buttons per platform conventions, but
		# doesn't rearrange the tab order for us. So, we do it manually:
		buttons = []
		for child in buttonSizer.GetChildren():
			win = child.GetWindow()
			if win is not None:
				buttons.append(win)
		buttons[1].MoveAfterInTabOrder(buttons[0])

		sz.append((0, sz.Border/2))
		sz.append(buttonSizer, "expand")
		sz.append((0, sz.Border))

		self.layout()

	
	def addControls(self):
		"""Use this method to add controls to the dialog. 

		The OK/Cancel	buttons will be added after this method runs, so that they 
		appear at the bottom of the dialog.
		"""
		pass
		
		
	def onOK(self, evt):
		self.Accepted = True
		self.EndModal(kons.DLG_OK)

	def onCancel(self, evt):
		self.Accepted = False
		self.EndModal(kons.DLG_CANCEL)

	def _getAccepted(self):
		return self._accepted		

	def _setAccepted(self, val):
		self._accepted = val
	
	Accepted = property(_getAccepted, _setAccepted, None,
			_("Specifies whether the user accepted the dialog, or canceled."))


if __name__ == "__main__":
	import test
	test.Test().runTest(dDialog)
	test.Test().runTest(dOkCancelDialog)
