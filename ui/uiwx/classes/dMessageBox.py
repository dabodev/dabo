''' dMessageBox.py

    Common message box dialog classes, such as "Are you sure?"
    along with convenience functions to allow calling like:
        if dAreYouSure("Delete this record"):
'''
import wx

class dMessageBox(wx.MessageDialog):
    def __init__(self, message, title, style):
        mainForm = wx.GetApp().GetTopWindow()
        wx.MessageDialog.__init__(self, mainForm, message, title, style)


def areYouSure(message="Are you sure?", defaultNo=False, cancelButton=False):
    style = wx.YES_NO|wx.ICON_QUESTION
    if cancelButton:
        style = style|wx.CANCEL
    if defaultNo:
        style = style|wx.NO_DEFAULT

    dlg = dMessageBox(message, "Dabo", style)
        
    retval = dlg.ShowModal()
    #dlg.Destroy()

    if retval in (wx.ID_YES, wx.ID_OK):
        return True
    elif retval in (wx.ID_NO,):
        return False
    else:
        return None

def stop(message="Stop"):
    style = wx.OK|wx.ICON_HAND
    dlg = dMessageBox(message, "Dabo", style)
    retval = dlg.ShowModal()
    return None
    
if __name__ == "__main__":
    app = wx.PySimpleApp()
    print dAreYouSure("Are you happy?")
    print dAreYouSure("Are you sure?", cancelButton=True)
    print dAreYouSure("So you aren't sad?", defaultNo=True)
