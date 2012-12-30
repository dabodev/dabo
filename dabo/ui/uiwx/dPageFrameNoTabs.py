# -*- coding: utf-8 -*-
import dabo

from dabo.ui import makeDynamicProperty
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
from dPage import dPage
from dPanel import dPanel
import dabo.dEvents as dEvents
import dabo.dColors as dColors
from dabo.dLocalize import _


class dPageFrameNoTabs(dPanel):
	"""
	Creates a pageframe with no tabs or other way for the user to select a
	page. Your code will have to programatically set the page.
	"""
	def __init__(self, *args, **kwargs):
		self._pageClass = dPage
		self._pageSizerClass = dabo.ui.dSizer
		self._activePage = None
		self._pages = []
		super(dPageFrameNoTabs, self).__init__(*args, **kwargs)
		self._baseClass = dPageFrameNoTabs


	def _afterInit(self):
		if self.Sizer is None:
			self.Sizer = dabo.ui.dSizer()
		super(dPageFrameNoTabs, self)._afterInit()


	def appendPage(self, pgCls=None, makeActive=False):
		"""
		Creates a new page, which should be a subclass of dPage. If makeActive
		is True, the page is displayed; otherwise, it is added without changing
		the SelectedPage.
		"""
		return self.insertPage(self.PageCount, pgCls=pgCls, makeActive=makeActive)


	def insertPage(self, pos, pgCls=None, makeActive=False, ignoreOverride=False):
		"""
		Inserts the page into the pageframe at the specified position,
		and makes it the active (displayed) page if makeActive is True.
		"""
		# Allow subclasses to potentially override this behavior. This will
		# enable them to handle page creation in their own way. If overridden,
		# the method will return the new page.
		ret = None
		if not ignoreOverride:
			ret = self._insertPageOverride(pos, pgCls, makeActive)
		if ret:
			return ret
		if pgCls is None:
			pgCls = self.PageClass
		if self.Sizer is None:
			self.Sizer = dabo.ui.dSizer()
		if isinstance(pgCls, dPage):
			pg = pgCls
		else:
			# See if the 'pgCls' is either some XML or the path of an XML file
			if isinstance(pgCls, basestring):
				xml = pgCls
				from dabo.lib.DesignerClassConverter import DesignerClassConverter
				conv = DesignerClassConverter()
				pgCls = conv.classFromText(xml)
			pg = pgCls(self)
		self.Sizer.insert(pos, pg, 1, "x")
		self._pages.insert(pos, pg)
		self.layout()
		if makeActive or (self.PageCount == 1):
			self.showPage(pg)
		else:
			self.showPage(self.SelectedPage)
		return self.Pages[pos]
	def _insertPageOverride(self, pos, pgCls, makeActive): pass


	def removePage(self, pgOrPos, delPage=True):
		"""
		Removes the specified page. You can specify a page by either
		passing the page itself, or a position. If delPage is True (default),
		the page is released, and None is returned. If delPage is
		False, the page is returned.
		"""
		if isinstance(pgOrPos, int):
			pg = self.Pages[pgOrPos]
		else:
			pg = pgOrPos
		self._pages.remove(pg)
		if delPage:
			pg.release()
			ret = None
		else:
			self.Sizer.remove(pg)
			ret = pg
		return ret


	def layout(self):
		"""Wrap the wx version of the call, if possible."""
		for pg in self.Pages:
			try:
				pg.layout()
			except AttributeError:
				# could be that the page is a single control, not a container
				pass
		super(dPageFrameNoTabs, self).layout()


	def showPage(self, pg):
		ap = self._activePage
		if isinstance(pg, int):
			pg = self.Pages[pg]
		newPage = (pg is not ap)
		if pg in self.Pages:
			if newPage:
				if ap:
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
			pg.setFocus()
		else:
			raise AttributeError(_("Attempt to show non-member page"))


	def nextPage(self):
		"""
		Selects the next page. If the last page is selected,
		it will select the first page.
		"""
		self.cyclePages(1)


	def priorPage(self):
		"""
		Selects the previous page. If the first page is selected,
		it will select the last page.
		"""
		self.cyclePages(-1)


	def cyclePages(self, num):
		"""
		Moves through the pages by the specified amount, wrapping
		around the ends. Negative values move to previous pages; positive
		move through the next pages.
		"""
		self.SelectedPageNumber = (self.SelectedPageNumber + num) % self.PageCount


	def getPageNumber(self, pg):
		"""Given a page, returns its position."""
		try:
			ret = self.Pages.index(pg)
		except ValueError:
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
	def _getPageClass(self):
		return self._pageClass

	def _setPageClass(self, val):
		if isinstance(val, basestring):
			from dabo.lib.DesignerClassConverter import DesignerClassConverter
			conv = DesignerClassConverter()
			self._pageClass = conv.classFromText(val)
		elif issubclass(val, (dPage, dPanel)):
			self._pageClass = val


	def _getPageCount(self):
		return len(self._pages)

	def _setPageCount(self, val):
		diff = (val - len(self._pages))
		if diff > 0:
			# Need to add pages
			while diff:
				self.appendPage()
				diff -= 1
		elif diff < 0:
			currPg = self.SelectedPageNumber
			pagesToKill = self._pages[val:]
			self._pages = self._pages[:val]
			# Need to add the check if the page exists since it
			# may have already been released.
			[pg.release() for pg in pagesToKill if pg]
			# Make sure the page we were on isn't one of the deleted pages.
			# If so, switch to the last page.
			newPg = min(currPg, val-1)
			self.SelectedPage = newPg


	def _getPages(self):
		return self._pages


	def _getPageSizerClass(self):
		return self._pageSizerClass

	def _setPageSizerClass(self, val):
		if self._constructed():
			self._pageSizerClass = val
		else:
			self._properties["PageSizerClass"] = val


	def _getSelectedPage(self):
		try:
			return self._activePage
		except AttributeError:
			return None

	def _setSelectedPage(self, pg):
		self.showPage(pg)


	def _getSelectedPageNumber(self):
		return self.getPageNumber(self._activePage)

	def _setSelectedPageNumber(self, val):
		pg = self.Pages[val]
		self.showPage(pg)


	PageClass = property(_getPageClass, _setPageClass, None,
			_("The default class used when adding new pages.  (dPage)") )

	PageCount = property(_getPageCount, _setPageCount, None,
			_("Returns the number of pages in this pageframe  (int)") )

	Pages = property(_getPages, None, None,
			_("List of all the pages.   (list)") )

	PageSizerClass = property(_getPageSizerClass, _setPageSizerClass, None,
			_("""Default sizer class for pages added automatically to this control. Set
			this to None to prevent sizers from being automatically added to child
			pages. (dSizer or None)"""))

	SelectedPage = property(_getSelectedPage, _setSelectedPage, None,
			_("Returns a reference to the currently displayed page  (dPage | dPanel)") )

	SelectedPageNumber = property(_getSelectedPageNumber, _setSelectedPageNumber, None,
			_("Returns a reference to the index of the currently displayed page  (int)") )


	DynamicPageClass = makeDynamicProperty(PageClass)
	DynamicPageCount = makeDynamicProperty(PageCount)
	DynamicSelectedPage = makeDynamicProperty(SelectedPage)
	DynamicSelectedPageNumber = makeDynamicProperty(SelectedPageNumber)



import random
class TestPage(dPage):
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
		pgf.PageCount = 12
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
		hsz.appendSpacer(4)
		hsz.append(bn, 1)
		hsz.appendSpacer(24)
		lbl = dabo.ui.dLabel(self, Caption="Select Page:")
		hsz.append(lbl)
		dd = dabo.ui.dDropdownList(self, DataSource=pgf,
				DataField="SelectedPageNumber", ValueMode="Position",
				Choices=["%s" % ii for ii in xrange(pgf.PageCount)])
		hsz.append(dd)
		self.Sizer.append(hsz, halign="center", border=8)
		self.layout()


	def onPriorPage(self, evt):
		self.pgf.priorPage()
		self.update()

	def onNextPage(self, evt):
		self.pgf.nextPage()
		self.update()


def main():
	from dabo.dApp import dApp
	app = dApp()
	app.MainFormClass = TestForm
	app.setup()
	app.start()

if __name__ == '__main__':
	main()

