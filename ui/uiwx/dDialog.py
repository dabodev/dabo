
import wx
import dabo
#dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
import dabo.dConstants as k

class dDialog(wx.Dialog, dabo.ui.dPemMixin):
	_IsContainer = True
	
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dDialog
		self._modal = True
		self._centered = True
		self._fit = True

		try:
			style = style | wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
		except:
			style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER

		preClass = wx.PreDialog
		dabo.ui.dPemMixin.__init__(self, preClass, parent, properties=properties, 
				style=style, *args, **kwargs)

	def _initEvents(self):
		self.Bind(wx.EVT_ACTIVATE, self.__onWxActivate)
		self.Bind(wx.EVT_CLOSE, self.__onWxClose)
		self.bindEvent(dEvents.Activate, self.__onActivate)
		self.bindEvent(dEvents.Close, self.__onClose)
		
	def _afterInit(self):
		super(dDialog, self)._afterInit()
		self.Sizer = dabo.ui.dSizer("V")
		# Hook method, so that we add the buttons last
		self._addControls()

	def __onWxClose(self, evt):
		self.raiseEvent(dEvents.Close, evt)
		
	def __onWxActivate(self, evt):
		""" Raise the Dabo Activate or Deactivate appropriately.
		"""
		if bool(evt.GetActive()):
			self.raiseEvent(dEvents.Activate, evt)
		else:
			self.raiseEvent(dEvents.Deactivate, evt)
			
	def __onActivate(self, evt): 
		if hasattr(self, "GetStatusBar"):
			if self.GetStatusBar() is None and self.ShowStatusBar:
				self.CreateStatusBar()

	def __onClose(self, evt):
		if self.Application is not None:
			self.Application.uiForms.remove(self)
		
	def show(self):
		if self.AutoSize:
			self.Fit()
		if self.Centered:
			self.Centre()
		if self.Modal:
			return self.ShowModal()
		else:
			return self.Show(True)

	def _addControls(self):
		"""Any controls that need to be added to the dialog 
		can be added in this method in framework classes, or
		in addControls() in instances.
		"""
		self.addControls()
	
	def addControls(self): pass
	

	def _getAutoSize(self):
		return self._fit
	def _setAutoSize(self, val):
		self._fit = val
	def _getCaption(self):
		return self.GetTitle()
	def _setCaption(self, val):
		self.SetTitle(val)
	def _getCentered(self):
		return self._centered
	def _setCentered(self, val):
		self._centered = val
	def _getModal(self):
		return self._modal
	def _setModal(self, val):
		self._modal = val
	
	AutoSize = property(_getAutoSize, _setAutoSize, None,
			"When True, the dialog resizes to fit the added controls.  (bool)")
	Caption = property(_getCaption, _setCaption, None,
			"The text that appears in the dialog's title bar  (str)" )
	Centered = property(_getCentered, _setCentered, None,
			"Determines if the dialog is displayed centered on the screen.  (bool)")
	Modal = property(_getModal, _setModal, None,
			"Determines if the dialog is shown modal (default) or modeless.  (bool)")



class dOkCancelDialog(dDialog):
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dOkCancelDialog
		super(dOkCancelDialog, self).__init__(parent=parent, properties=properties, *args, **kwargs)


	def _addControls(self):
		# We want every subclass to be able to add their controls
		# before we add the OK/Cancel buttons.
		super(dOkCancelDialog, self)._addControls()

		pnl = dabo.ui.dPanel(self)
		hs = dabo.ui.dSizer("H")
		pnl.Sizer = hs
		hs.append( (24, 1) )
		self.btnOK = dabo.ui.dCommandButton(pnl, Caption="OK")
		self.btnOK.bindEvent(dEvents.Hit, self.OnOK)
		hs.append(self.btnOK, 1)
		hs.append( (16, 1) )
		self.btnCancel = dabo.ui.dCommandButton(pnl, Caption="Cancel")
		self.btnCancel.bindEvent(dEvents.Hit, self.OnCancel)
		hs.append(self.btnCancel, 1)
		hs.append( (24, 1) )
		
		pnl.Layout()
		pnl.Fit()
		# Add a little breathing room
		pnl.Width += 4
		pnl.Height += 4
		pnl.Layout()
		
		# Add a 10-pixel spacer between the added controls and 
		# the OK/Cancel button panel
		self.Sizer.append( (1, 10) )		
		self.Sizer.append(pnl, 0, alignment=("bottom", "right") )#, border=20)
		self.Sizer.append( (1, 20) )		
		
		self.Layout()
		
	
	def addControls(self):
		"""Use this method to add controls to the dialog. The OK/Cancel
		buttons will be added after this method runs, so that they appear 
		at the bottom of the dialog
		"""
		pass
		
	def OnOK(self, evt):
		self.EndModal(k.DLG_OK)
	def OnCancel(self, evt):
		self.EndModal(k.DLG_CANCEL)
		
		

if __name__ == "__main__":
	import test
 	test.Test().runTest(dDialog)
	test.Test().runTest(dOkCancelDialog)
