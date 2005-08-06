import wx

def getIconBitmap(fileName, setMask=True):
	r = wx.Image(fileName, wx.BITMAP_TYPE_PNG)
	r.SetMask(setMask)
	return r.ConvertToBitmap()

app = wx.PySimpleApp()

form = wx.Frame(None, -1)
pf = wx.Notebook(form)

il = wx.ImageList(16, 16, initialCount=0)

for image in ("edit.png", "edit1.png"): 
	print "Adding image '%s'..." % image
	bmp = getIconBitmap(image)
	print "bmp ok?:", bmp.Ok()
	print il.Add(bmp)
pf.AssignImageList(il)


pf.AddPage(wx.Panel(pf), "grey alpha mask", imageId=0)
pf.AddPage(wx.Panel(pf), "black alpha mask", imageId=1)



form.Show()
app.MainLoop()
