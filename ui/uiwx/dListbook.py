import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
import dPage
import dabo.dEvents as dEvents
from dabo.dLocalize import _

class dListbook(wx.Listbook, cm.dControlMixin):
	""" Create a container for an unlimited number of pages.
	"""
	_IsContainer = True
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dListbook
		preClass = wx.PreListbook
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

		
	def _afterInit(self):
		super(dListbook, self)._afterInit()
		self.lastSelection = 0
		self.PageCount = 3
	
	
	def _initEvents(self):
		super(dListbook, self)._initEvents()
		self.Bind(wx.EVT_LISTBOOK_PAGE_CHANGED, self.__onPageChanged)

				
	def __onPageChanged(self, evt):
		evt.Skip()
		evt.StopPropagation()

		newPageNum = evt.GetSelection()
		oldPageNum = self._lastPage
		
		self.__pageChanged(newPageNum, oldPageNum)

		
	def __pageChanged(self, newPageNum, oldPageNum):		
		self._lastPage = newPageNum
		
		self.GetPage(newPageNum).raiseEvent(dEvents.PageEnter)
		if oldPageNum is not None:
			self.GetPage(oldPageNum).raiseEvent(dEvents.PageLeave)
		
	
	# property get/set functions:
	def _getPageClass(self):
		try:
			return self._pageClass
		except AttributeError:
			return dPage.dPage
			
	def _setPageClass(self, value):
		if issubclass(value, dControlMixin.dControlMixin):
			self._pageClass = value
		else:
			raise TypeError, 'PageClass must descend from a Dabo base class.'
			
			
	def _getPageCount(self):
		return int(self.GetPageCount())
		
	def _setPageCount(self, value):
		if self._constructed():
			value = int(value)
			pageCount = self.GetPageCount()
			pageClass = self.PageClass
		
			if value < 0:
				raise ValueError, "Cannot set PageCount to less than zero."
		
			if value > pageCount:
				for i in range(pageCount, value):
					self.AddPage(pageClass(self), "Page %s" % (i+1,))
			elif value < pageCount:
				for i in range(pageCount, value, -1):
					self.DeletePage(i-1)
					self.Refresh()
		else:
			self._properties["PageCount"] = value	
		

	def _getTabPosition(self):
		if self.hasWindowStyleFlag(wx.LB_BOTTOM):
			return 'Bottom'
		elif self.hasWindowStyleFlag(wx.LB_RIGHT):
			return 'Right'
		elif self.hasWindowStyleFlag(wx.LB_LEFT):
			return 'Left'
		else:
			return 'Top'

	def _getTabPositionEditorInfo(self):
		return {'editor': 'list', 'values': ['Top', 'Left', 'Right', 'Bottom']}

	def _setTabPosition(self, value):
		value = str(value)

		self.delWindowStyleFlag(wx.LB_BOTTOM)
		self.delWindowStyleFlag(wx.LB_RIGHT)
		self.delWindowStyleFlag(wx.LB_LEFT)

		if value == 'Top':
			pass
		elif value == 'Left':
			self.addWindowStyleFlag(wx.LB_LEFT)
		elif value == 'Right':
			self.addWindowStyleFlag(wx.LB_RIGHT)
		elif value == 'Bottom':
			self.addWindowStyleFlag(wx.LB_BOTTOM)
		else:
			raise ValueError, ("The only possible values are "
						"'Top', 'Left', 'Right', and 'Bottom'")

	# Property definitions:
	PageClass = property(_getPageClass, _setPageClass, None,
		"""Specifies the class of control to use for pages by default.
		
		This really only applies when using the PageCount property to set the
		number of pages. If you instead use AddPage() you still need to send
		an instance as usual. Class must descend from a dabo base class.
		""")
						
	PageCount = property(_getPageCount, _setPageCount, None, 
		"""Specifies the number of pages in the listbook.
		
		When using this to increase the number of pages, an instance of
		self.PageClass will be used as the page object.
		""")
						
	TabPosition = property(_getTabPosition, _setTabPosition, None, 
		"""Specifies where the page tabs are located.
		    
		Valid values are:
			Top (default)
		    Left
		    Right
		    Bottom
		""")
