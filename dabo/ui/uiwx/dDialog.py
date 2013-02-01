# -*- coding: utf-8 -*-
import warnings
import wx
import dabo
if __name__ == "__main__":
	import dabo.ui
	dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
import dabo.dConstants as kons
from dabo.dLocalize import _
import dFormMixin as fm
import dPemMixin as pm
from dabo.ui import makeDynamicProperty


class dDialog(fm.dFormMixin, wx.Dialog):
	"""
	Creates a dialog, which is a lightweight form.

	Dialogs are like forms, but typically are modal and are requesting a very
	specific piece of information from the user, and/or offering specific
	information to the user.
	"""
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dDialog
		self._modal = True
		self._centered = True
		self._fit = True
		self._borderless = self._extractKey((properties, kwargs), "Borderless", False)

		if self._borderless:
			defaultStyle = wx.STAY_ON_TOP
		else:
			defaultStyle = wx.DEFAULT_DIALOG_STYLE
		try:
			kwargs["style"] = kwargs["style"] | defaultStyle
		except KeyError:
			kwargs["style"] = defaultStyle

		preClass = wx.PreDialog
		fm.dFormMixin.__init__(self, preClass, parent, properties=properties,
				*args, **kwargs)

		# Hook method, so that we add the buttons last
		self._addControls()

		# Needed starting with wx 2.7, for the first control to have the focus:
		self.setFocus()


	def getBizobj(self, *args, **kwargs):
		## self.Form resolves to the containing dialog, making calls to 'self.Form.getBizobj()'
		## fail since the dialog knows nothing about bizobjs. Let's be helpful and pass the
		## request up to the form:
		return self.Form.getBizobj(*args, **kwargs)


	def EndModal(self, *args, **kwargs):
		self.saveSizeAndPosition()
		self.hide()
		if self.Modal:
			try:
				super(dDialog, self).EndModal(*args, **kwargs)
			except wx._core.PyAssertionError:
				# The modal hack is causing problems in some edge cases.
				pass


	def _afterInit(self):
		self.MenuBarClass = None
		self.Sizer = dabo.ui.dSizer("V")
		super(dDialog, self)._afterInit()


	def ShowModal(self):
		self.restoreSizeAndPositionIfNeeded()
		# updates were potentially suppressed while the dialog
		# wasn't visible, so update now.
		self.update()
		return super(dDialog, self).ShowModal()


	def showModal(self):
		"""Show the dialog modally."""
		## pkm: We had to override this, because the default in dPemMixin doesn't
		##      actually result in a modal dialog.
		self.Modal = True
		self.show()


	def showModeless(self):
		"""Show the dialog non-modally."""
		self.Modal = False
		self.show()


	def _afterShow(self):
		if self.AutoSize:
			self.Fit()
		if self.Centered:
			self.Centre()


	def show(self):
		# Call _afterShow() once immediately, and then once after the dialog is visible, which
		# will correct minor mistakes such as the height of wordwrapped labels not being
		# accounted for. If we only called it after the dialog was already shown, then we
		# risk the dialog being too jumpy.
		self._afterShow()
		dabo.ui.callAfter(self._afterShow)
		if self.Modal:
			ret = self.ShowModal()
			return {wx.ID_OK: kons.DLG_OK, wx.ID_CANCEL: kons.DLG_CANCEL}.get(ret, ret)
		return self.Show(True)



	def _addControls(self):
		"""
		Any controls that need to be added to the dialog
		can be added in this method in framework classes, or
		in addControls() in instances.
		"""
		self.beforeAddControls()
		self.addControls()
		self.afterAddControls()


	def beforeAddControls(self):
		"""This is a hook, called at the appropriate time by the framework."""
		pass


	def afterAddControls(self):
		"""This is a hook, called at the appropriate time by the framework."""
		pass


	def addControls(self):
		"""
		Add your custom controls to the dialog.

		This is a hook, called at the appropriate time by the framework.
		"""
		pass


	def release(self):
		"""
		Need to augment this to make sure the dialog
		is removed from the app's forms collection.
		"""
		if self.Application is not None:
			self.Application.uiForms.remove(self)
		super(dDialog, self).release()


	def _controlGotFocus(self, ctrl):
		# Placeholder until we unify dForm and dDialog
		pass


	def _getAutoSize(self):
		return self._fit

	def _setAutoSize(self, val):
		self._fit = val


	def _getBorderless(self):
		return self._borderless

	def _setBorderless(self, val):
		if self._constructed():
			raise ValueError(_("Cannot set the Borderless property once the dialog is created."))
		else:
			self._properties["Borderless"] = val


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


	def _getShowStat(self):
		# Dialogs cannot have status bars.
		return False
	_showStatusBar	= property(_getShowStat)


	AutoSize = property(_getAutoSize, _setAutoSize, None,
			_("When True, the dialog resizes to fit the added controls.  (bool)"))

	Borderless = property(_getBorderless, _setBorderless, None,
			_("""Must be passed at construction time. When set to True, the dialog displays
			without a title bar or borders  (bool)"""))

	Caption = property(_getCaption, _setCaption, None,
			_("The text that appears in the dialog's title bar  (str)") )

	Centered = property(_getCentered, _setCentered, None,
			_("Determines if the dialog is displayed centered on the screen.  (bool)"))

	Modal = property(_getModal, _setModal, None,
			_("Determines if the dialog is shown modal (default) or modeless.  (bool)"))


	DynamicAutoSize = makeDynamicProperty(AutoSize)
	DynamicCaption = makeDynamicProperty(Caption)
	DynamicCentered = makeDynamicProperty(Centered)



class dStandardButtonDialog(dDialog):
	"""
	Creates a dialog with standard buttons and associated functionality. You can
	choose the buttons that display by passing True for any of the following
	properties:

		OK
		Cancel
		Yes
		No
		Help

	If you don't specify buttons, only the OK will be included; if you do specify buttons,
	you must specify them all; in other words, OK is only assumed if nothing is specified.
	Then add your custom controls in the addControls() hook method, and respond to
	the pressing of the standard buttons in the run*() handlers, where * is the name of the
	associated property (e.g., runOK(), runNo(), etc.). You can query the Accepted property
	to find out if the user pressed "OK" or "Yes"; if neither of these was pressed,
	Accepted will be False.
	"""
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._ok = self._extractKey((properties, kwargs), "OK")
		self._cancel = self._extractKey((properties, kwargs), "Cancel")
		self._yes = self._extractKey((properties, kwargs), "Yes")
		self._no = self._extractKey((properties, kwargs), "No")
		self._help = self._extractKey((properties, kwargs), "Help")
		# Check for both OK and Yes. This simply does not work, at least with wxPython.
		if self._ok and self._yes:
			raise ValueError(_("Dialogs cannot have both 'OK' and 'Yes' buttons."))
		self._cancelOnEscape = True
		super(dStandardButtonDialog, self).__init__(parent=parent, properties=properties, *args, **kwargs)
		self._baseClass = dStandardButtonDialog
		self._accepted = False


	def _addControls(self):
		# By default, don't intercept the esc key.
		self.setEscapeButton(None)

		# Set some default Sizer properties (user can easily override):
		sz = self.Sizer
		sz.DefaultBorder = 20
		sz.DefaultBorderLeft = sz.DefaultBorderRight = True
		sz.append((0, sz.DefaultBorder))

		# Add the specified buttons. If none were specified, then just add OK
		ok = self._ok
		cancel = self._cancel
		yes = self._yes
		no = self._no
		help = self._help
		if (ok is None and cancel is None and yes is None and
				no is None and help is None):
			ok = True

		flags = 0
		if ok:
			flags = flags | wx.OK
		if cancel:
			flags = flags | wx.CANCEL
		if yes:
			flags = flags | wx.YES
		if no:
			flags = flags | wx.NO
		if help:
			flags = flags | wx.HELP
		if flags == 0:
			# Nothing specified; default to just OK
			flags = wx.OK
		# Initialize the button references
		self.btnOK = self.btnCancel = self.btnYes = self.btnNo = self.btnHelp = None

		# We need a Dabo sizer to wrap the wx sizer.
		self.stdButtonSizer = dabo.ui.dSizer()
		sbs = self.CreateButtonSizer(flags)
		self.stdButtonSizer.append1x(sbs)

		btns = [b.GetWindow() for b in sbs.GetChildren() if b.IsWindow()]
		for btn in btns:
			id_ = btn.GetId()
			if id_ == wx.ID_YES:
				self.btnYes = newbtn = dabo.ui.dButton(btn.Parent)
				mthd = self._onYes
			elif id_ == wx.ID_NO:
				self.btnNo = newbtn = dabo.ui.dButton(btn.Parent)
				mthd = self._onNo
			elif id_ == wx.ID_OK:
				self.btnOK = newbtn = dabo.ui.dButton(btn.Parent)
				mthd = self._onOK
			elif id_ == wx.ID_CANCEL:
				self.btnCancel = newbtn = dabo.ui.dButton(btn.Parent)
				mthd = self._onCancel
			elif id_ == wx.ID_HELP:
				self.btnHelp = btn
				newbtn = None
				mthd = self._onHelp
			if newbtn is None:
				# Only the Help button cannot be wrapped, as it is platform-specific in appearance.
				btn.Bind(wx.EVT_BUTTON, mthd)
			else:
				newbtn.Caption = btn.GetLabel()
				pos = dabo.ui.getPositionInSizer(btn)
				sz = btn.GetContainingSizer()
				sz.Replace(btn, newbtn)
				btn.Destroy()
				newbtn.bindEvent(dEvents.Hit, mthd)
		if ok:
			self.OKButton.DefaultButton = True
		elif yes:
			self.YesButton.DefaultButton = True

		# Force the escape button to be set appropriately:
		self.CancelOnEscape = self.CancelOnEscape

		# Wx rearranges the order of the buttons per platform conventions, but
		# doesn't rearrange the tab order for us. So, we do it manually:
		buttons = []
		for child in sbs.GetChildren():
			win = child.GetWindow()
			if win is not None:
				buttons.append(win)
		for pos, btn in enumerate(buttons[1:]):
			btn.MoveAfterInTabOrder(buttons[pos-1])

		# Let the user add their controls
		super(dStandardButtonDialog, self)._addControls()

		# Just in case user changed Self.Sizer, update our reference:
		sz = self.Sizer
		if self.ButtonSizerPosition is None:
			# User code didn't add it, so we must.
			if sz.DefaultBorder:
				spacer = sz.DefaultBorder
			else:
				spacer = 10
			bs = dabo.ui.dSizer("v")
			bs.append((0, spacer/2))
			bs.append(self.ButtonSizer, "x")
			bs.append((0, spacer))
			sz.append(bs, "x")
		self.layout()


	def setEscapeButton(self, btn=None):
		"""
		Set which button gets hit when Esc pressed.

		CancelOnEscape must be True for this to work.
		"""
		if not self.CancelOnEscape or not btn:
			self.SetEscapeId(wx.ID_NONE)
		else:
			self.SetEscapeId(btn.GetId())



	################################################
	#    Handlers for the standard buttons.
	################################################
	# Note that onOK() and
	# onCancel() are the names of the old event handlers, and
	# code has been written to use these. So as not to break this
	# older code, we issue a deprecation warning and call the
	# old handler.
	def _onOK(self, evt):
		self.Accepted = True
		self.activeControlValid()
		try:
			self.onOK()
		except TypeError:
			warnings.warn(_("The onOK() handler is deprecated. Use the runOK() method instead"),
				Warning)
			self.onOK(None)
		except AttributeError:
			# New code should not have onOK
			pass
		if self.runOK() is not False:
			self.EndModal(kons.DLG_OK)

	def _onCancel(self, evt):
		self.Accepted = False
		self.activeControlValid()
		try:
			self.onCancel()
		except TypeError:
			warnings.warn(_("The onCancel() handler is deprecated. Use the runCancel() method instead"),
				Warning)
			self.onCancel(None)
		except AttributeError:
			# New code should not have onCancel
			pass

		if self.runCancel() is not False:
			self.EndModal(kons.DLG_CANCEL)
		else:
			evt.stop()
	def _onYes(self, evt):
		self.Accepted = True
		if self.runYes() is not False:
			self.EndModal(kons.DLG_YES)

	def _onNo(self, evt):
		self.Accepted = False
		if self.runNo() is not False:
			self.EndModal(kons.DLG_NO)
		else:
			evt.stop()

	def _onHelp(self, evt):
		self.runHelp()

	# The following are stub methods that can be overridden when needed.
	def runOK(self): pass
	def runCancel(self): pass
	def runYes(self): pass
	def runNo(self): pass
	def runHelp(self): pass
	################################################


	def addControls(self):
		"""
		Use this method to add controls to the dialog. The standard buttons will be added
		after this method runs, so that they appear at the bottom of the dialog.
		"""
		pass


	def addControlSequence(self, seq):
		"""
		This takes a sequence of 3-tuples or 3-lists, and adds controls
		to the dialog as a grid of labels and data controls. The first element of
		the list/tuple is the prompt, the second is the data type, and the third
		is the RegID used to retrieve the entered value.
		"""
		gs = dabo.ui.dGridSizer(HGap=5, VGap=8, MaxCols=2)
		for prmpt, typ, rid in seq:
			chc = None
			gs.append(dabo.ui.dLabel(self, Caption=prmpt), halign="right")
			if typ in (int, long):
				cls = dabo.ui.dSpinner
			elif typ is bool:
				cls = dabo.ui.dCheckBox
			elif isinstance(typ, list):
				cls = dabo.ui.dDropdownList
				chc = typ
			else:
				cls = dabo.ui.dTextBox
			ctl = cls(self, RegID=rid)
			gs.append(ctl)
			if chc:
				ctl.Choices = chc
		gs.setColExpand(True, 1)
		self.Sizer.insert(self.LastPositionInSizer, gs, "x")
		self.layout()


	def _getAccepted(self):
		return self._accepted

	def _setAccepted(self, val):
		self._accepted = val


	def _getButtonSizer(self):
		return getattr(self, "stdButtonSizer", None)


	def _getButtonSizerPosition(self):
		return self.ButtonSizer.getPositionInSizer()


	def _getCancelButton(self):
		return self.btnCancel


	def _getCancelOnEscape(self):
		return self._cancelOnEscape

	def _setCancelOnEscape(self, val):
		if self._constructed():
			self._cancelOnEscape = val
			self.setEscapeButton(None)
			if val:
				for trial in (self.btnCancel, self.btnNo):
					if trial is not None:
						self.setEscapeButton(trial)
						break
		else:
			self._properties["CancelOnEscape"] = val


	def _getHelpButton(self):
		return self.btnHelp


	def _getOKButton(self):
		return self.btnOK


	def _getNoButton(self):
		return self.btnNo


	def _getYesButton(self):
		return self.btnYes


	Accepted = property(_getAccepted, _setAccepted, None,
			_("Specifies whether the user accepted the dialog, or canceled.  (bool)"))

	ButtonSizer = property(_getButtonSizer, None, None,
			_("Returns a reference to the sizer controlling the Ok/Cancel buttons.  (dSizer)"))

	ButtonSizerPosition = property(_getButtonSizerPosition, None, None,
			_("""Returns the position of the Ok/Cancel buttons in the sizer.  (int)"""))

	CancelButton = property(_getCancelButton, None, None,
			_("Reference to the Cancel button on the form, if present  (dButton or None)."))

	CancelOnEscape = property(_getCancelOnEscape, _setCancelOnEscape, None,
			_("""When True (default), pressing the Escape key will perform the same action
			as clicking the Cancel button. If no Cancel button is present but there is a No button,
			the No behavior will be executed. If neither button is present, the default button's
			action will be executed  (bool)"""))

	HelpButton = property(_getHelpButton, None, None,
			_("Reference to the Help button on the form, if present  (dButton or None)."))

	NoButton = property(_getNoButton, None, None,
			_("Reference to the No button on the form, if present  (dButton or None)."))

	OKButton = property(_getOKButton, None, None,
			_("Reference to the OK button on the form, if present  (dButton or None)."))

	YesButton = property(_getYesButton, None, None,
			_("Reference to the Yes button on the form, if present  (dButton or None)."))



class dOkCancelDialog(dStandardButtonDialog):
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		kwargs["Yes"] = kwargs["No"] = False
		kwargs["OK"] = kwargs["Cancel"] = True
		super(dOkCancelDialog, self).__init__(parent, properties, *args, **kwargs)
		self._baseClass = dOkCancelDialog



class dYesNoDialog(dStandardButtonDialog):
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		kwargs["Yes"] = kwargs["No"] = True
		kwargs["OK"] = kwargs["Cancel"] = False
		super(dYesNoDialog, self).__init__(parent, properties, *args, **kwargs)
		self._baseClass = dYesNoDialog



class _FloatDialog(dDialog):
	def __init__(self, owner, *args, **kwargs):
		self._above = None
		self._owner = None
		kwargs["Borderless"] = True
		kwargs["FloatOnParent"] = True
		super(_FloatDialog, self).__init__(*args, **kwargs)


	def clear(self):
		"""Releases any controls remaining from a previous usage."""
		self.Sizer.clear(True)


	def show(self):
		# position by owner
		if self.Owner is None:
			self.Centered = True
		else:
			self.Centered = None
			left, top = self.Owner.absoluteCoordinates()
			self.Left = left
			if self.Above:
				self.Bottom = top
			else:
				self.Top = top + self.Owner.Height
		# Make sure that we're within the display limits
		maxW, maxH = dabo.ui.getDisplaySize()
		self.Left = max(5, self.Left)
		self.Top = max(5, self.Top)
		self.Right = min(self.Right, maxW-5)
		self.Bottom = min(self.Bottom, maxH-5)
		dabo.ui.callAfterInterval(10, self._resetPosition, self.Position)
		super(_FloatDialog, self).show()

	def _resetPosition(self, pos):
		"""
		On gtk at least, something in wxPython sets Position to centered
		otherwise.
		"""
		self.Position = pos
		
	def _getAbove(self):
		return self._above

	def _setAbove(self, val):
		if self._constructed():
			self._above = val
		else:
			self._properties["Above"] = val


	def _getOwner(self):
		return self._owner

	def _setOwner(self, val):
		if self._constructed():
			self._owner = val
		else:
			self._properties["Owner"] = val


	Above = property(_getAbove, _setAbove, None,
			_("Is this dialog positioned above its owner? Default=False  (bool)"))

	Owner = property(_getOwner, _setOwner, None,
			_("Control which is currently managing this window.  (varies)"))








if __name__ == "__main__":
	import test
	test.Test().runTest(dDialog)
	test.Test().runTest(dStandardButtonDialog)
	test.Test().runTest(dOkCancelDialog)
	test.Test().runTest(dYesNoDialog)
