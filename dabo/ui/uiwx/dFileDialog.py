# -*- coding: utf-8 -*-
import wx
import dabo
import dabo.dConstants as kons
from dabo.dLocalize import _


class OsDialogMixin(object):
	def _beforeInit(self):
		self._dir = self._fname = self._msg = self._path = self._wildcard = ""
		super(OsDialogMixin, self)._beforeInit()


	def show(self):
		self._dir = self._fname = self._path = ""
		ret = kons.DLG_CANCEL
		res = self.ShowModal()
		if res ==  wx.ID_OK:
			ret = kons.DLG_OK
			if self._multiple:
				self._path = self.GetPaths()
			else:
				self._path = self.GetPath()
			if self._exposeFiles:
				self._dir = self.GetDirectory()
				if self._multiple:
					self._fname = self.GetFilenames()
				else:
					self._fname = self.GetFilename()
		return ret


	def release(self):
		self.Destroy()


	def _getDir(self):
		return self._dir

	def _setDir(self, dir):
		if self._exposeFiles:
			self.SetDirectory(dir)


	def _getFileName(self):
		return self._fname

	def _setFileName(self, fn):
		if self._exposeFiles:
			self.SetFilename(fn)


	def _getMessage(self):
		return self._msg

	def _setMessage(self, msg):
		self.SetMessage(msg)


	def _getPath(self):
		return self._path

	def _setPath(self, pth):
		self.SetPath(pth)


	def _getWildcard(self):
		return self._wildcard

	def _setWildcard(self, txt):
		if self._exposeFiles:
			self.SetWildcard(txt)


	Directory = property(_getDir, _setDir, None,
			_("The directory of the selected file or files (str)"))

	FileName = property(_getFileName, _setFileName, None,
			_("The name of the selected file (str) or files (tuple of strs)"))

	Message = property(_getMessage, _setMessage, None,
			_("The prompt displayed to the user.  (str)"))

	Path = property(_getPath, _setPath, None,
			_("The full path of the selected file (str)  or files (tuple of strs)"))

	Wildcard = property(_getWildcard, _setWildcard, None,
			_("The wildcard that will limit the files displayed in the dialog.  (str)"))



class dFileDialog(OsDialogMixin, wx.FileDialog):
	"""Creates a file dialog, which asks the user to choose a file."""
	_exposeFiles = True

	def __init__(self, parent=None, message=_("Choose a file"), defaultPath="",
			defaultFile="", wildcard="*.*", multiple=False, style=wx.OPEN):
		self._baseClass = dFileDialog
		if multiple:
			# wxPython changed the constant after 2.6
			try:
				multStyle = wx.FD_MULTIPLE
			except AttributeError:
				multStyle = wx.MULTIPLE
			style = style | multStyle

			self._multiple = True
		else:
			self._multiple = False
		if parent is None:
			parent = dabo.dAppRef.ActiveForm
		super(dFileDialog, self).__init__(parent=parent, message=message,
				defaultDir=defaultPath, defaultFile=defaultFile,
				wildcard=wildcard, style=style)


class dFolderDialog(OsDialogMixin, wx.DirDialog):
	"""Creates a folder dialog, which asks the user to choose a folder."""
	_exposeFiles = False


	def __init__(self, parent=None, message=_("Choose a folder"),
			defaultPath="", wildcard="*.*"):
		self._multiple = False
		self._baseClass = dFolderDialog
		if parent is None:
			parent = dabo.dAppRef.ActiveForm
		super(dFolderDialog, self).__init__(parent=parent, message=message,
				defaultPath=defaultPath, style=wx.DD_NEW_DIR_BUTTON)


class dSaveDialog(dFileDialog):
	"""Creates a save dialog, which asks the user to specify a file to save to."""
	def __init__(self, parent=None, message=_("Save to:"), defaultPath="",
			defaultFile="", wildcard="*.*", style=wx.SAVE):
		self._baseClass = dSaveDialog
		if parent is None:
			parent = dabo.dAppRef.ActiveForm
		super(dSaveDialog, self).__init__(parent=parent, message=message,
				defaultPath=defaultPath, defaultFile=defaultFile,
				wildcard=wildcard, style=style)



if __name__ == "__main__":
	import test
	test.Test().runTest(dFileDialog)
	test.Test().runTest(dFolderDialog)
	test.Test().runTest(dSaveDialog)
