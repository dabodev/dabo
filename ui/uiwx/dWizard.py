import dabo
from dabo.dLocalize import _
import dabo.dEvents as dEvents
import dabo.dConstants as k

dabo.ui.loadUI("wx")


class dWizard(dabo.ui.dForm):
	""" This is the main form for creating wizards. To use it, define
	a series of wizard pages, based on dWizardPage. Then add these
	classes to your subclass of dWizard. The order that you add them 
	will be the order that they appear in the wizard.
	"""
	
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		pgs = self.extractKey(kwargs, "Pages")
		self.iconName = self.extractKey(kwargs, "Icon")
		# Add the main panel
		kwargs["Panel"] = True
		
		super(dWizard, self).__init__(parent=parent, properties=properties, *args, **kwargs)
		
		self._pages = []
		self._currentPage = None
		
		self.setup()
		if pgs:
			self.append(pgs)
		
	
	def setup(self):
		""" This creates the controls used by the wizard. """
		if not self.iconName:
			self.self.iconName = "empty"
		self.wizardIcon = dabo.ui.dIcons.getIconBitmap(self.iconName)
			
	
	def append(self, pg):
		if type(pg) in (list, tuple):
			for p in pg:
				self.append(p)
		else:
			self._pages.append(pg(self.mainPanel))
			pg.Visible = False
	
	
	def insert(self, pos, pg):
		if type(pg) in (list, tuple):
			pg.reverse()
			for p in pg:
				self.insert(pos, p)
		else:
			self._pages.insert(pos, pg(self.mainPanel))
			pg.Visible = False


	# Property methods
	def _getCurrPage(self):
		return self._currentPage
	def _setCurrPage(self, pg):
		self._currentPage = pg
		
	def _getNextPage(self):
		return self._currentPage.NextPage
		
	def _getPrevPage(self):
		return self._currentPage.PrevPage

	CurrentPage = property(_getCurrPage, _setCurrPage, None,
			_("Current Page in the wizard  (dWizardPage)") )

	NextPage = property(_getNextPage, None, None,
			_("Page to navigate if the user clicks 'next'  (dWizardPage)") )

	PrevPage = property(_getPrevPage, None, None,
			_("Page to navigate if the user clicks 'back'  (dWizardPage)") )

