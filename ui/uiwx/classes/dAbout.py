''' dAbout.py

    About screen.

'''
import sys

import wx
import wx.html
import wx.lib.wxpTag
from dForm import dForm

class dAbout(dForm):
    text = '''
<html>
<body bgcolor="#AC76DE">
<center><table bgcolor="#458154" width="100%%" cellspacing="0"
cellpadding="0" border="1">
<tr>
    <td align="center">
    <h1>%s</h1>
    </td>
</tr>
</table>


<P>&nbsp;</P>

</center>

<TABLE BORDER=0>
<TR>
    <TD ALIGN="RIGHT">
    <font size=-1>%s Version:</font>
    </TD>
    <TD ALIGN="LEFT"><B>%s</B></TD>
</TR>
<TR>
    <TD ALIGN="RIGHT">
    <font size=-1>wxPython Version:</FONT>
    </TD>
    <TD ALIGN="LEFT"><B>%s</B></TD>
</TR>
<TR>
    <TD ALIGN="RIGHT">
    <font size=-1>Python Version:</FONT>
    </TD>
    <TD ALIGN="LEFT"><B>%s</B></TD>
</TR>
<TR>
    <TD ALIGN="RIGHT">
    <font size=-1>Platform:</FONT>
    </TD>
    <TD ALIGN="LEFT"><B>%s</B></TD>
</TR>
</TABLE>

<p align="right"><wxp module="wx" class="Button">
    <param name="label" value="Okay">
    <param name="id"    value="ID_OK">
</wxp></p>

</body>
</html>
'''
    def __init__(self, parent, dApp=None):
        dForm.__init__(self, parent)
        html = wx.html.HtmlWindow(self, -1, size=(420, -1))
        py_version = sys.version.split()[0]
        if dApp:
            dabo_version = dApp.getAppInfo("appVersion")
            dabo_appName = dApp.getAppInfo("appName")
        else:
            dabo_version = "?"
            dabo_appName = "Dabo"
        self.SetLabel("About %s" % dabo_appName)
        html.SetPage(self.text % (dabo_appName, dabo_appName,
            dabo_version, wx.VERSION_STRING, 
            py_version, sys.platform))
        btn = html.FindWindowById(wx.ID_OK)
        btn.SetDefault()
        ir = html.GetInternalRepresentation()
        html.SetSize( (ir.GetWidth()+25, ir.GetHeight()+25) )
        self.SetClientSize(html.GetSize())
        self.CentreOnParent(wx.BOTH)

#---------------------------------------------------------------------------



if __name__ == '__main__':
    app = wx.PySimpleApp()
    dlg = dAbout(None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()

