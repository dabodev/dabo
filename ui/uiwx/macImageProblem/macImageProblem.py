import wx

def getIconBitmap(fileName, setMask=True):
	r = wx.Image(fileName, wx.BITMAP_TYPE_PNG)
	r.SetMask(setMask)
	return r.ConvertToBitmap()

app = wx.PySimpleApp()

form = wx.Frame(None, -1)
pf = wx.Notebook(form)

il = wx.ImageList(16, 16, initialCount=0)
il.Add(getIconBitmap("checkMark.png"))
il.Add(getIconBitmap("browse.png"))
il.Add(getIconBitmap("edit.png"))
pf.AssignImageList(il)


pf.AddPage(wx.Panel(pf), "select", imageId=0)
pf.AddPage(wx.Panel(pf), "browse", imageId=1)
pf.AddPage(wx.Panel(pf), "edit", imageId=2)
form.Show()
app.MainLoop()
