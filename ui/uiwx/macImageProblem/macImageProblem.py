import wx

def getIconBitmap(fileName, setMask=True):
	r = wx.Image(fileName, wx.BITMAP_TYPE_PNG)
	r.SetMask(setMask)
	return r.ConvertToBitmap()

app = wx.PySimpleApp()

form = wx.Frame(None, -1)
pf = wx.Notebook(form)

il = wx.ImageList(16, 16, initialCount=0)

for image in ("checkMark.png", "browse.png", "edit.png", 
              "checkMark1.png", "edit1.png"):
	print "Adding image '%s'..." % image
	bmp = getIconBitmap(image)
	print "bmp ok?:", bmp.Ok()
	print il.Add(bmp)
pf.AssignImageList(il)


pf.AddPage(wx.Panel(pf), "select", imageId=0)
pf.AddPage(wx.Panel(pf), "browse", imageId=1)
pf.AddPage(wx.Panel(pf), "edit", imageId=2)
pf.AddPage(wx.Panel(pf), "select 1", imageId=3)
pf.AddPage(wx.Panel(pf), "edit 1", imageId=4)



form.Show()
app.MainLoop()
