import wx
import dabo
#dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
import dabo.dConstants as k

class dDialog(wx.Dialog):
	_IsContainer = True
	
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dDialog
		self.BaseClass = dDialog
		super(dDialog,self).__init__(parent=parent, style=wx.DEFAULT_DIALOG_STYLE)
		self.Centre()
		self._modal = True
		self.Sizer = dabo.ui.dSizer("vertical")
	
	def show(self):
		if self._modal:
			return self.ShowModal()
		else:
			return self.Show(True)
	
	def _getCaption(self):
		return self.GetTitle()
	def _setCaption(self, val):
		self.SetTitle(val)
	def _getModal(self):
		return self._modal
	def _setModal(self, val):
		self._modal = val
	
	Caption = property(_getCaption, _setCaption, None,
			"The text that appears in the dialog's title bar  (str)" )
	Modal = property(_getModal, _setModal, None,
			"Determines if the dialog is shown modal (default) or modeless.  (bool)")



class dOkCancelDialog(dDialog):
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dOkCancelDialog
		self.BaseClass = dOkCancelDialog
		super(dOkCancelDialog, self).__init__(parent=parent, properties=properties)
		
		# Hook method, so that we add the buttons last
		self.addControls()
		
		hs = dabo.ui.dSizer("H")
		self.btnOK = dabo.ui.dCommandButton(self, Caption="OK")
		hs.append(self.btnOK, 0, "expand")
		self.btnOK.bindEvent(dEvents.Hit, self.OnOK)
		hs.append( (16, 1) )

		self.btnCancel = dabo.ui.dCommandButton(self, Caption="Cancel")
		self.btnCancel.bindEvent(dEvents.Hit, self.OnCancel)
		hs.append(self.btnCancel, 0, "expand")
		
		self.Sizer.append(hs, 0, "expand", alignment=("bottom", "middle"), border=10)
		
		self.Layout()
		w, h = self.GetSize()
		self.Sizer.SetDimension(0, 0, w, h)
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
