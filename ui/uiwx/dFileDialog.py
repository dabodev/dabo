import wx
import dabo.dConstants as k


class dFileDialog(wx.FileDialog):
	_IsContainer = False
	
	def __init__(self, parent=None, message="Choose a file", defaultDir="", 
			defaultFile="", wildcard="*.*", style=wx.OPEN):
		self._baseClass = dFileDialog
		super(dFileDialog, self).__init__(parent=parent, message=message, 
				defaultDir=defaultDir, defaultFile=defaultFile, 
				wildcard=wildcard, style=style)
		self._dir = self._fname = self._msg = self._path = self._wildcard = ""

	
	def show(self):
		res = self.ShowModal()
		if res ==  wx.ID_OK:
			ret = k.DLG_OK
			self._dir = self.GetDirectory()
			self._fname = self.GetFilename()
			self._path = self.GetPath()
		else:	
			self._dir = self._fname = self._path = ""
			ret = k.DLG_CANCEL
		return ret
		

	def _getDir(self):
		return self._dir
	def _setDir(self, dir):
		self.SetDirectory(dir)
	
	def _getFileName(self):
		return self._fname
	def _setFileName(self, fn):
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


class dSaveDialog(dFileDialog):
	def __init__(self, parent=None, message="Save to:", defaultDir="", 
			defaultFile="", wildcard="*.*", style=wx.SAVE):
		self._baseClass = dSaveDialog
		super(dSaveDialog, self).__init__(parent=parent, message=message, 
				defaultDir=defaultDir, defaultFile=defaultFile, 
				wildcard=wildcard, style=style)
		self._dir = self._fname = self._msg = self._path = self._wildcard = ""
