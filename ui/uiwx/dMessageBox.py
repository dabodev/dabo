""" dMessageBox.py

Common message box dialog classes, such as "Are you sure?"
along with convenience functions to allow calling like:
	if dAreYouSure("Delete this record"):
"""
import wx

class dMessageBox(wx.MessageDialog):
	def __init__(self, message, title, style):
		mainForm = wx.GetApp().GetTopWindow()
		if mainForm:
			activeForm = mainForm.FindFocus()
			if activeForm:
				form = activeForm
			else:
				form = mainForm
		else:
			form = mainForm

		wx.MessageDialog.__init__(self, form, message, title, style)
		

def areYouSure(message="Are you sure?", title="Dabo",
			defaultNo=False, cancelButton=True):
	style = wx.YES_NO|wx.ICON_QUESTION
	if cancelButton:
		style = style|wx.CANCEL
	if defaultNo:
		style = style|wx.NO_DEFAULT

	dlg = dMessageBox(message, title, style)

	retval = dlg.ShowModal()
	dlg.Destroy()

	if retval in (wx.ID_YES, wx.ID_OK):
		return True
	elif retval in (wx.ID_NO,):
		return False
	else:
		return None


def stop(message="Stop", title="Dabo"):
	style = wx.OK|wx.ICON_HAND
	dlg = dMessageBox(message, title, style)
	retval = dlg.ShowModal()
	dlg.Destroy()
	return None


def info(message="Information", title="Dabo"):
	style = wx.OK|wx.ICON_INFORMATION
	dlg = dMessageBox(message, title, style)
	retval = dlg.ShowModal()
	dlg.Destroy()
	return None

	
if __name__ == "__main__":
	app = wx.PySimpleApp()
	print areYouSure("Are you happy?")
	print areYouSure("Are you sure?", cancelButton=True)
	print areYouSure("So you aren\'t sad?", defaultNo=True)
