import wx, dPanel, dTimer
import dabo.dEvents as dEvents


class dPage(dPanel.dScrollPanel):
	""" Create a page to appear as a tab in a dPageFrame.
	"""
	def __init__(self, parent, name="dPage"):
		dPage.doDefault(parent, name=name)


	def afterInit(self):
		self.initSizer()
		self.itemsCreated = False
		dPage.doDefault()
		
	def initEvents(self):
		dPage.doDefault()
		self.bindEvent(dEvents.PageEnter, self.onPageEnter)
		self.bindEvent(dEvents.PageLeave, self.onPageLeave)

	def initSizer(self):
		""" Set up the default vertical box sizer for the page.
		"""
		self.SetSizer(wx.BoxSizer(wx.VERTICAL))


	def createItems(self):
		""" Create the controls in the page.

		Called when the page is entered for the first time, allowing subclasses
		to delay-populate the page.
		"""
		pass


	def onPageEnter(self, event):
		""" Occurs when this page becomes the active page.

		Subclasses may override or extend.
		"""
		if not self.itemsCreated:
			self.createItems()
			self.itemsCreated = True
			self.GetSizer().Layout()
			
			# Needed on Linux to get the sizer to layout:
			self.Size = (-1,-1)

						
	def onPageLeave(self, event):
		""" Occurs when this page will no longer be the active page.

		Subclasses may override.
		"""
		if hasattr(self, "Form"):
			self.Form.activeControlValid()
			

	def onValueRefresh(self, event):
		""" Occurs when the dForm asks dControls to refresh themselves.

		While dPage isn't a data-aware control, this may be useful information
		to act upon.
		"""
		pass
	
	
	def _getPagePosition(self):
		""" Returns the position of this page within its parent.
		"""
		parent = self.Parent
		cnt = parent.GetPageCount()
		ret = -1
		for i in range(cnt):
			if parent.GetPage(i) == self:
				ret = i
				break
		return ret
	

	def _getCaption(self):
		# Need to determine which page we are
		ret = ""
		pos = self._getPagePosition()
		if pos > -1:
			ret = self.Parent.GetPageText(pos)
		return ret
	
	def _setCaption(self, val):
		pos = self._getPagePosition()
		if pos > -1:
			self.Parent.SetPageText(pos, val)
	
	Caption = property(_getCaption, _setCaption, None, 
			"The text identifying this particular page")

