import wx, dIcons
import dPageFrame as pgf
import dPageDataNav as pag

class dPageFrameDataNav(pgf.dPageFrame):

	def __init__(self, parent, name='dPageFrameDataNav'):
		dPageFrameDataNav.doDefault(parent, name=name)


	def afterInit(self):
		self.addDefaultPages()
		dPageFrameDataNav.doDefault()


	def addDefaultPages(self):
		''' Add the standard pages to the pageframe.

		Subclasses may override or extend.
		'''
		il = wx.ImageList(16, 16, initialCount=0)
		il.Add(dIcons.getIconBitmap('checkMark'))
		il.Add(dIcons.getIconBitmap('browse'))
		il.Add(dIcons.getIconBitmap('edit'))
		il.Add(dIcons.getIconBitmap('childview'))

		self.AssignImageList(il)
		self.AddPage(pag.dSelectPage(self), 'Select', imageId=0)
		self.AddPage(pag.dBrowsePage(self), 'Browse', imageId=1)
		self.AddPage(pag.dEditPage(self), 'Edit', imageId=2)

		bizobj = self.Parent.getBizobj()
		for child in bizobj.getChildren():
			self.AddPage(pag.dChildViewPage(self), child.Caption, imageId=3)
			
		self.GetPage(0).onEnterPage()

