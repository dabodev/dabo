""" dMenu.py """
import wx
import dPemMixin as pm
import dIcons

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

	def prependSeparator(self):
		self.PrependSeparator()
	
	def appendSeparator(self):
		self.AppendSeparator()
	
	def appendMenu(self, prompt, menu, help=""):
		self.AppendMenu(-1, prompt, menu, helpStr=help)
		
	def prepend(self, prompt, bindobj=None, func=None, 
			help="", bmp=None, menutype=""):
		return self.addOne(self.Prepend, prompt, bindobj, func, help, bmp, menutype)
		
	def append(self, prompt, bindobj=None, func=None, 
			help="", bmp=None, menutype=""):
		return self.addOne(self.Append, prompt, bindobj, func, help, bmp, menutype)
	
	def addOne(self, addFunc, prompt, bindobj, func, help, bmp, menutype):
		itmtyp = self.getItemType(menutype)
		itm = addFunc(-1, prompt, help=help, kind=itmtyp)
		if bindobj and func:
			bindobj.Bind(wx.EVT_MENU, func, itm)
		if bmp:
			if type(bmp) == str:
				# Icon name was passed; get the actual bitmap
				bmp = dIcons.getIconBitmap(bmp)
			itm.SetBitmap(bmp)
		return itm
			
	
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

