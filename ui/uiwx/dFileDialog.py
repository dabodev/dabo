import wx
import dabo.dConstants as k


class OsDialogMixin:
	def __init__(self):
		self._dir = self._fname = self._msg = self._path = self._wildcard = ""

	def show(self):
		self._dir = self._fname = self._path = ""
		ret = k.DLG_CANCEL
		res = self.ShowModal()
		if res ==  wx.ID_OK:
			ret = k.DLG_OK
			self._path = self.GetPath()
			if self._exposeFiles:
				self._dir = self.GetDirectory()
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
			"The directory of the selected file.  (str)")
	
	FileName = property(_getFileName, _setFileName, None, 
			"The name of the selected file.  (str)")
	
	Message = property(_getMessage, _setMessage, None, 
			"The prompt displayed to the user.  (str)")

	Path = property(_getPath, _setPath, None, 
			"The full path of the selected file.  (str)")

	Wildcard = property(_getWildcard, _setWildcard, None, 
			"The wildcard that will limit the files displayed in the dialog.  (str)")



class dFileDialog(wx.FileDialog, OsDialogMixin):
	_IsContainer = False
	_exposeFiles = True
	
	def __init__(self, parent=None, message="Choose a file", defaultPath="", 
			defaultFile="", wildcard="*.*", style=wx.OPEN):
		self._baseClass = dFileDialog
		super(dFileDialog, self).__init__(parent=parent, message=message, 
				defaultDir=defaultPath, defaultFile=defaultFile, 
				wildcard=wildcard, style=style)

	
class dFolderDialog(wx.DirDialog, OsDialogMixin):
	_IsContainer = False
	_exposeFiles = False
	
	def __init__(self, parent=None, message="Choose a folder", 
			defaultPath="", wildcard="*.*"):
		self._baseClass = dFolderDialog
		super(dFolderDialog, self).__init__(parent=parent, message=message, 
				defaultPath=defaultPath, style=wx.DD_NEW_DIR_BUTTON)


class dSaveDialog(dFileDialog):
	def __init__(self, parent=None, message="Save to:", defaultPath="", 
			defaultFile="", wildcard="*.*", style=wx.SAVE):
		self._baseClass = dSaveDialog
		super(dSaveDialog, self).__init__(parent=parent, message=message, 
				defaultPath=defaultPath, defaultFile=defaultFile, 
				wildcard=wildcard, style=style)
#		self._dir = self._fname = self._msg = self._path = self._wildcard = ""

