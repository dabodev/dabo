""" dMenu.py """
import wx
import dPemMixin as pm

# wx constants for styles
dNormalItem = wx.ITEM_NORMAL
dCheckItem =  wx.ITEM_CHECK
dRadioItem = wx.ITEM_RADIO

class dMenu(wx.Menu, pm.dPemMixin):
	_IsContainer = False
	
	def __init__(self, mainForm=None):
		self.mainForm = mainForm
		if mainForm:
			self.actionList = mainForm.Application.actionList
		else:
			self.actionList = None
		super(dMenu, self).__init__()

	def appendSeparator(self):
		self.AppendSeparator()
	
	def appendMenu(self, prompt, menu, help=""):
		self.AppendMenu(-1, prompt, menu, helpStr=help)
		
	def append(self, prompt, func=None, hlp="", menutype=""):
		itmtyp = self.getItemType(menutype)
		self.Append(-1, prompt, help=hlp, kind=itmtyp)
		if func:
			self.Bind(wx.EVT_MENU, func)
	
	def insert(self, pos, prompt, help="", type=""):
		itmtyp = self.getItemType(typ)
		self.Insert(-1, pos, prompt, helpString=help, kind=itmtyp)
	
	def getItemType(self, typ):
		typ = str(typ).lower()[:3]
		ret = dNormalItem
		if typ in ("che", "chk"):
			ret = dCheckItem
		elif typ == "rad":
			# Currently only implemented under Windows and GTK, 
			# use #if wxHAS_RADIO_MENU_ITEMS to test for 
			# availability of this feature.
			ret = dRadioItem
		return ret

