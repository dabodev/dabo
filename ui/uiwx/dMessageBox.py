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


if __name__ == "__main__":
	app = wx.PySimpleApp()
	print areYouSure("Are you happy?")
	print areYouSure("Are you sure?", cancelButton=True)
	print areYouSure("So you aren\'t sad?", defaultNo=True)
