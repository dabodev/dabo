import dabo
dabo.ui.loadUI("wx")
import dPage
import dPanel
import dabo.dEvents as dEvents
import dabo.dColors as dColors
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


class dPageFrameNoTabs(dabo.ui.dPanel):
	"""Creates a pageframe with no tabs.

	Your code will have to programatically set the current page, because the
	user will have no way to do this.
	"""
	def __init__(self, *args, **kwargs):
		self._pageClass = dPage.dPage
		self._activePage = None
		super(dPageFrameNoTabs, self).__init__(*args, **kwargs)
		self._baseClass = dPageFrameNoTabs
		
		
	def _afterInit(self):
		if self.Sizer is None:
			self.Sizer = dabo.ui.dSizer()
		super(dPageFrameNoTabs, self)._afterInit()
		
		
	def appendPage(self, pgCls=None, makeActive=False):
		"""Creates a new page, which must be a subclass of dPanel
		or dPage. If makeActive is True, the page is displayed; 
		otherwise, it is added and hidden.
		"""
		return self.insertPage(self.PageCount, pgCls=pgCls, makeActive=makeActive)
		
	
	def insertPage(self, pos, pgCls=None, makeActive=False):
		""" Inserts the page into the pageframe at the specified position, 
		and makes it the active (displayed) page if makeActive is True.
		"""
		if pgCls is None:
			pgCls = self.PageClass
		if self.Sizer is None:
			self.Sizer = dabo.ui.dSizer()
		pg = pgCls(self)
		self.Sizer.insert(pos, pg, 1, "x")
		self.layout()
		if makeActive or (self.PageCount == 1):
			self.showPage(pg)
		else:
			self.showPage(self.SelectedPage)
		return self.Pages[pos]


	def showPage(self, pg):
		ap = self._activePage
		newPage = (pg is not ap)
		if pg in self.Pages:
			if newPage:
				if ap is not None:
					dabo.ui.callAfter(ap.raiseEvent, dEvents.PageLeave)
					apNum = self.getPageNumber(ap)
				else:
					apNum = -1
				dabo.ui.callAfter(pg.raiseEvent, dEvents.PageEnter)
				dabo.ui.callAfter(self.raiseEvent, dEvents.PageChanged, 
						oldPageNum=apNum, newPageNum=self.getPageNumber(pg))
				self._activePage = pg
			for ch in self.Pages:
				self.Sizer.Show(ch, (ch is pg))
			self.layout()
		else:
			raise AttributeError, _("Attempt to show non-member page")

	
	def nextPage(self):
		"""Selects the next page. If the last page is selected,
		it will select the first page.
		"""
		try:
			self.SelectedPageNumber += 1
		except IndexError:
			self.SelectedPageNumber = 0

	
	def priorPage(self):
		"""Selects the previous page. If the first page is selected,
		it will select the last page.
		"""
		try:
			self.SelectedPageNumber -= 1
		except IndexError:
			self.SelectedPage = self.Pages[-1]
	
	
	def getPageNumber(self, pg):
		"""Given a page, returns its position."""
		try:
			ret = self.Pages.index(pg)
		except:
			ret = None
		return ret


	#------------------------------------
	# The following methods don't do anything except
	# make this class compatible with dPage classes, which 
	# expect their parent to have these methods.
	#------------------------------------
	def getPageImage(self, pg):
		return None
	
	
	def setPageImage(self, pg, img):
		pass
	
	
	def GetPageText(self, pg):
		return ""
		
		
	def SetPageText(self, pg, txt):
		pass
	#------------------------------------
		
		
	def _getPgCls(self):
		return self._pageClass
	def _setPgCls(self, val):
		if issubclass(val, (dPage.dPage, dPanel.dPanel)):
			self._pageClass = val
	
	
	def _getPgCnt(self):
		return len(self.Children)
	def _setPgCnt(self, val):
		diff = (val - len(self.Children))
		if diff > 0:
			# Need to add pages
			for ii in range(diff):
				self.appendPage()
		elif diff < 0:
			# Need to remove pages. If the active page is one 
			# of those being removed, set the active page to the
			# last page.
			currPg = self.SelectedPage
			while len(self.Children) > val:
				self.Children[-1].release()
			if len(self.Children) < currPg:
				self.SelectedPage = self.Children[-1]
	
	
	def _getPages(self):
		return self.Children	
			
	
	def _getSel(self):
		try:
			return self._activePage
		except AttributeError:
			return None
			
	def _setSel(self, pg):
		self.showPage(pg)
	
	
	def _getSelNum(self):
		return self.getPageNumber(self._activePage)
			
	def _setSelNum(self, val):
		pg = self.Pages[val]
		self.showPage(pg)
	
	
	PageClass = property(_getPgCls, _setPgCls, None,
			_("The default class used when adding new pages.  (dPage)") )

	PageCount = property(_getPgCnt, _setPgCnt, None,
			_("Returns the number of pages in this pageframe  (int)") )
	
	Pages = property(_getPages, None, None,
			_("List of all the pages.   (list)") )

	SelectedPage = property(_getSel, _setSel, None,
			_("Returns a reference to the currently displayed page  (dPage | dPanel)") )

	SelectedPageNumber = property(_getSelNum, _setSelNum, None,
			_("Returns a reference to the index of the currently displayed page  (int)") )


	DynamicPageClass = makeDynamicProperty(PageClass)
	DynamicPageCount = makeDynamicProperty(PageCount)
	DynamicSelectedPage = makeDynamicProperty(SelectedPage)
	DynamicSelectedPageNumber = makeDynamicProperty(SelectedPageNumber)



import random
class TestPage(dPage.dPage):
	def afterInit(self):
		self.lbl = dabo.ui.dLabel(self, FontSize=36)
		color = random.choice(dColors.colorDict.keys())
		self.BackColor = self.lbl.Caption = color
		self.Sizer = sz = dabo.ui.dSizer("h")
		sz.appendSpacer(1, 1)
		sz.append(self.lbl, 1)
		sz.appendSpacer(1, 1)
	
	def setLabel(self, txt):
		self.lbl.Caption = txt
		self.layout()
		
	
class TestForm(dabo.ui.dForm):
	def afterInit(self):
		self.Caption = "Tabless Pageframe Example"
		self.pgf = pgf = dPageFrameNoTabs(self)
		pgf.PageClass = TestPage
		pgf.PageCount = 5
		idx = 0
		for pg in pgf.Pages:
			pg.setLabel("Page #%s" % idx)
			idx += 1
		self.Sizer.append1x(pgf)
		
		# Add prev/next buttons
		bp = dabo.ui.dButton(self, Caption="Prior")
		bp.bindEvent(dEvents.Hit, self.onPriorPage)
		bn = dabo.ui.dButton(self, Caption="Next")
		bn.bindEvent(dEvents.Hit, self.onNextPage)
		hsz = dabo.ui.dSizer("h")
		hsz.append(bp, 1)
		hsz.append(bn, 1)		
		self.Sizer.append(hsz, halign="center")
		self.layout()
		
		
	def onPriorPage(self, evt):
		self.pgf.priorPage()
		
	def onNextPage(self, evt):
		self.pgf.nextPage()
		

def main():
	app = dabo.dApp()
	app.MainFormClass = TestForm
	app.setup()
	app.start()

if __name__ == '__main__':
	main()

