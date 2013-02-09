# -*- coding: utf-8 -*-
"""
Common message box dialog classes, such as "Are you sure?"
along with convenience functions to allow calling like::

	if dAreYouSure("Delete this record"):

"""
import wx
import dabo
from dabo.dLocalize import _


def getForm():
	ret = dabo.dAppRef.ActiveForm
	if not ret:
		# Could be a dead object
		ret = None
	return ret


class dMessageBox(wx.MessageDialog):
	def __init__(self, message, title, style, parent=None, requestUserAttention=True,
				userAttentionMode=wx.USER_ATTENTION_INFO):
		if not parent:
			parent = getForm()
		if not wx.GetApp().IsActive() and isinstance(parent, (wx.Frame, wx.MDIParentFrame)) and requestUserAttention:
			# We only want to send the requestUserAttention to the OS if our application
			# isn't currently the active application. Otherwise it abuses the intent...
			parent.RequestUserAttention(userAttentionMode)
		# Force the message and title to strings
		message = "%s" % message
		title = "%s" % title
		wx.MessageDialog.__init__(self, parent, message, title, style)


def areYouSure(message="Are you sure?", title=None, defaultNo=False,
		cancelButton=True, parent=None, requestUserAttention=True):
	"""
	Display a dMessageBox asking the user to answer yes or no to a question.

	Returns True, False, or None, for choices "Yes", "No", or "Cancel".

	The default title comes from app.getAppInfo("appName"), or if the
	application object isn't available it will be "Dabo Application".

	If defaultNo is True, the 'No' button will be the default button.

	If cancelButton is True (default), a third 'Cancel' button will appear.

	If parent isn't passed, it will automatically resolve to the current
	active form.

	If requestUserAttention is True, if the operating system supports it,
	the taskbar will flash (Windows) or the dock item will jump (Mac),
	showing the user that your application needs attention.
	"""
	if title is None:
		title = getDefaultTitle()
	style = wx.YES_NO|wx.ICON_QUESTION
	if cancelButton:
		style = style|wx.CANCEL
	else:
		style = style & ~wx.CANCEL
	if defaultNo:
		style = style|wx.NO_DEFAULT

	dlg = dMessageBox(message, title, style, parent=parent)
	retval = dlg.ShowModal()
	dlg.Destroy()

	if retval in (wx.ID_YES, wx.ID_OK):
		return True
	elif retval in (wx.ID_NO,):
		return False
	else:
		return None


def stop(message="Stop", title=None, parent=None, requestUserAttention=True):
	"""
	Display a dMessageBox informing the user that the operation cannot proceed.

	Returns None.

	The default title comes from app.getAppInfo("appName"), or if the
	application object isn't available it will be "Dabo Application".

	If parent isn't passed, it will automatically resolve to the current
	active form.

	If requestUserAttention is True, if the operating system supports it,
	the taskbar will flash (Windows) or the dock item will jump (Mac),
	showing the user that your application needs attention.
	"""
	if title is None:
		title = getDefaultTitle()
	icon = wx.ICON_HAND
	showMessageBox(message=message, title=title, icon=icon, parent=parent,
			requestUserAttention=requestUserAttention)

def info(message="Information", title=None, parent=None, requestUserAttention=True):
	"""
	Display a dMessageBox offering the user some useful information.

	Returns None.

	The default title comes from app.getAppInfo("appName"), or if the
	application object isn't available it will be "Dabo Application".

	If parent isn't passed, it will automatically resolve to the current
	active form.

	If requestUserAttention is True, if the operating system supports it,
	the taskbar will flash (Windows) or the dock item will jump (Mac),
	showing the user that your application needs attention.
	"""
	if title is None:
		title = getDefaultTitle()
	icon = wx.ICON_INFORMATION
	showMessageBox(message=message, title=title, icon=icon, parent=parent,
			requestUserAttention=requestUserAttention)

def exclaim(message="Important!", title=None, parent=None,
			requestUserAttention=True):
	"""
	Display a dMessageBox urgently informing the user that we cannot proceed.

	Returns None.

	The default title comes from app.getAppInfo("appName"), or if the
	application object isn't available it will be "Dabo Application".

	If parent isn't passed, it will automatically resolve to the current
	active form.

	If requestUserAttention is True, if the operating system supports it,
	the taskbar will flash (Windows) or the dock item will jump (Mac),
	showing the user that your application needs attention.
	"""
	if title is None:
		title = getDefaultTitle()
	icon = wx.ICON_EXCLAMATION
	showMessageBox(message=message, title=title, icon=icon, parent=parent,
			requestUserAttention=requestUserAttention,
			userAttentionMode=wx.USER_ATTENTION_ERROR)


def showMessageBox(message, title, icon, parent=None,
			requestUserAttention=True, userAttentionMode=wx.USER_ATTENTION_INFO):
	style = wx.OK | icon
	dlg = dMessageBox(message, title, style, parent=parent,
			requestUserAttention=requestUserAttention,
			userAttentionMode=userAttentionMode)
	dlg.CenterOnParent()
	retval = dlg.ShowModal()
	dlg.Destroy()
	return None


def getDefaultTitle():
	"""
	Get a default title for the messageboxes.

	Comes from app.getAppInfo("appName"), or if the application
	object isn't available the title will be "Dabo Application".
	"""
	ret = None
	if dabo.dAppRef:
		ret = dabo.dAppRef.getAppInfo("appName")
	if ret is None:
		ret = "Dabo Application"
	return ret


if __name__ == "__main__":
	from dabo.dApp import dApp
	app = dApp()
	app.showMainFormOnStart = False
	app.setup()
	print areYouSure("Are you happy?")
	print areYouSure("Are you sure?", cancelButton=False)
	print areYouSure("So you aren\'t sad?", defaultNo=True)

	# Test requesting user attention:
	frm = dabo.ui.dForm()
	def onExit(evt):
		app.onFileExit(evt)
	cap = _("After you click okay, switch to another running application\nwithin 5 seconds, to test"
			" the requestUserAttention setting.\n\n\nAfterwards, click the button below to exit.")
	lbl = dabo.ui.dLabel(frm, Caption=cap)
	ln = dabo.ui.dLine(frm, Orientation="H", Height=3)
	btn = dabo.ui.dButton(frm, Caption=_("Exit"), OnHit=onExit)
	frm.Sizer.append(lbl, halign="center", border=20)
	frm.Sizer.append(ln, "x", halign="center", border=120, borderSides=["left", "right"])
	frm.Sizer.appendSpacer(80)
	frm.Sizer.append(btn, halign="center")
	frm.layout()
	dabo.ui.callAfterInterval(5000, exclaim, "Abort! Abort!", parent=frm)
	frm.show()
	app.start()
