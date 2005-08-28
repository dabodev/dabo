""" dMessageBox.py

Common message box dialog classes, such as "Are you sure?"
along with convenience functions to allow calling like:
	if dAreYouSure("Delete this record"):
"""
import wx

def getForm():
		mainForm = wx.GetApp().GetTopWindow()
		if mainForm:
			activeForm = mainForm.FindFocus()
			if activeForm:
				form = activeForm
			else:
				form = mainForm
		else:
			form = mainForm


class dMessageBox(wx.MessageDialog):
	def __init__(self, message, title, style):
		form = getForm()
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
	icon = wx.ICON_HAND
	showMessageBox(message=message, title=title, icon=icon)

def info(message="Information", title="Dabo"):
	icon = wx.ICON_INFORMATION
	showMessageBox(message=message, title=title, icon=icon)

def exclaim(message="Important!", title="Dabo"):
	icon = wx.ICON_EXCLAMATION
	showMessageBox(message=message, title=title, icon=icon)

def showMessageBox(message, title, icon):
	style = wx.OK | icon
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
