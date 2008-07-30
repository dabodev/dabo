# -*- coding: utf-8 -*-
import wx
from dabo.dLocalize import _

class dDropTarget(wx.DropTarget):
	def __init__(self):
		wx.DropTarget.__init__(self)
		
		self._fileHandle  = self._textHandle = None
		
		self.compositeDataObject = wx.DataObjectComposite()
		self.fileData = wx.FileDataObject()
		self.compositeDataObject.Add(self.fileData)
		self.textData = wx.TextDataObject()
		self.compositeDataObject.Add(self.textData)
		
		self.SetDataObject(self.compositeDataObject)
	
	def OnData(self, x, y, defResult):
		if self.GetData():
			format = self.compositeDataObject.ReceivedFormat.GetType()
			print "Data type = %s, file type = %s" % (format, wx.DF_FILENAME)
			if format == wx.DF_FILENAME:
				print "dropping files to file handle: %s" % self._fileHandle
				if self._fileHandle:
					self._fileHandle.processDroppedFiles(self.fileData.Filenames)
			elif format == wx.DF_TEXT or wx.DF_HTML:
				self._textHandle.processDroppedText(self.textData.Text)
		else:
			print false
		
		return defResult
	
	def OnDragOver(self, xpos, ypos, result):
		return wx.DragLink
	
	#Property getters and setters
	def _getFileHandler(self):
		return self._fileHandle
	
	def _setFileHandler(self, val):
		self._fileHandle = val
	
	
	def _getTextHandler(self):
		return self._textHandle
	
	def _setTextHandler(self, val):
		self._textHandle = val
	
	
	#PropertyDefinitions
	FileHandler = property(_getFileHandler, _setFileHandler, None,
		_("""Reference to the object that will handle files dropped on this control.
			When files are dropped, a list of them will be passed to this object's 
			'processDroppedFiles()' method. Default=None  (object or None)"""))
	
	TextHandler = property(_getTextHandler, _setTextHandler, None,
		_("""Reference to the object that will handle text dropped on this control.
			When text is dropped, that text will be passed to this object's 
			'processDroppedText()' method. Default=None  (object or None)"""))