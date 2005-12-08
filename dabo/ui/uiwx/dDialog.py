import wx
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
import dabo.dConstants as kons
from dabo.dLocalize import _
import dFormMixin as fm


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
		

	def hide(self):
		self.Show(False)
		

	def _onEscape(self, evt):
		if self.ReleaseOnEscape:
			self.release()


	def _addControls(self):
		"""Any controls that need to be added to the dialog 
		can be added in this method in framework classes, or
		in addControls() in instances.
		"""
		self.addControls()
	
	def addControls(self): pass


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

	Caption = property(_getCaption, _setCaption, None,
			"The text that appears in the dialog's title bar  (str)" )

	Centered = property(_getCentered, _setCentered, None,
			"Determines if the dialog is displayed centered on the screen.  (bool)")

	Modal = property(_getModal, _setModal, None,
			"Determines if the dialog is shown modal (default) or modeless.  (bool)")
	
	ReleaseOnEscape = property(_getReleaseOnEscape, _setReleaseOnEscape, None,
			"Determines if the <Esc> key releases the dialog (the default).")



class dOkCancelDialog(dDialog):
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dOkCancelDialog
		self._accepted = False
		super(dOkCancelDialog, self).__init__(parent=parent, properties=properties, *args, **kwargs)


	def _addControls(self):
		# We want every subclass to be able to add their controls
		# before we add the OK/Cancel buttons.
		self.pnlControl = dabo.ui.dPanel(self, BackColor="yellow")
		self.pnlControl.Sizer = dabo.ui.dSizer("v")
		self.pnlButtons = pnl = dabo.ui.dPanel(self)
		pnl.Sizer = hs = dabo.ui.dSizer("H")
		self.btnOK = dabo.ui.dButton(pnl, id=wx.ID_OK)
		self.btnOK.bindEvent(dEvents.Hit, self.onOK)
		hs.appendSpacer(20, 1)
		hs.append(self.btnOK, 1)
		hs.appendSpacer(5)
		self.btnCancel = dabo.ui.dButton(pnl, id=wx.ID_CANCEL)
		self.btnCancel.bindEvent(dEvents.Hit, self.onCancel)
		hs.append(self.btnCancel, 1)
		hs.appendSpacer(8)
		pnl.layout()
		pnl.Fit()
		
		sz = self.Sizer
		sz.Border = 20
		sz.BorderLeft = sz.BorderRight = True
		sz.appendSpacer(10, 1)
		sz.append(self.pnlControl, 10, "x")
		sz.appendSpacer(10, 1)
		sz.append(self.pnlButtons, 0, halign="right", valign="bottom", 
				border=16, borderFlags=("right", "bottom"))
		
		# This is the point where the user adds controls.
		super(dOkCancelDialog, self)._addControls()

		self.layout()

	
	def addControls(self):
		"""Use this method to add controls to the dialog. The OK/Cancel
		buttons will be added after this method runs, so that they appear 
		at the bottom of the dialog
		"""
		pass
		
		
	def onOK(self, evt):
		self.Accepted = True
		self.EndModal(kons.DLG_OK)
	# Create an alias to this method.
	onAccept = onOK

	def onCancel(self, evt):
		self.Accepted = False
		self.EndModal(kons.DLG_CANCEL)

	def _getAccepted(self):
		return self._accepted		

	def _setAccepted(self, val):
		self._accepted = val
	
	Accepted = property(_getAccepted, _setAccepted)


if __name__ == "__main__":
	import test
	test.Test().runTest(dDialog)
	test.Test().runTest(dOkCancelDialog)
