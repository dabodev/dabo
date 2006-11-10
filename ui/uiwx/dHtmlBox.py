import wx.html
import os
import types
import dabo
from dabo.dLocalize import _

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
from dabo.ui import makeDynamicProperty

class dHtmlWindow(wx.html.HtmlWindow, cm.dControlMixin):
    """Creates a scrolled panel that can load and display html pages

    The Html Window can load any html text, file, or url that is fed to it.
    """
    def __init__(self, parent, properties=None, *args, **kwargs):
        self._horizontalScroll = self._verticalScroll = True
        self._baseClass = dHtmlWindow
        preClass = wx.html.PreHtmlWindow
        if "style" not in kwargs:
            kwargs["style"] = wx.TAB_TRAVERSAL
        cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
        self.SetScrollRate(10, 10)
    #		self.SetScrollbars(10, 10, -1, -1)


    def layout(self):
        """ Wrap the wx version of the call, if possible. """
        self.Layout()
        for child in self.Children:
            try:
                child.layout()
            except: pass
        try:
            # Call the Dabo version, if present
            self.Sizer.layout()
        except:
            pass


    def _getChildren(self):
        ret = super(dHtmlWindow, self)._getChildren()
        return [kid for kid in ret
                if isinstance(kid, dabo.ui.dPemMixinBase.dPemMixinBase)]

    def _setChildren(self, val):
        super(dHtmlWindow, self)._setChildren(val)


    def _getHorizontalScroll(self):
        return self._horizontalScroll

    def _setHorizontalScroll(self, val):
        self._horizontalScroll = val
        self.EnableScrolling(self._horizontalScroll, self._verticalScroll)
        rt = self.GetScrollPixelsPerUnit()
        self.SetScrollRate({True:rt[0], False:0}[val], rt[1])


    def _getPage(self):
        return self.GetOpenedPage()

    def _setPage(self, val):
        if isinstance(val, types.StringType):
            if val[:7] == "http://":
                super(dHtmlWindow, self).LoadPage(val)
            elif os.path.exists(val):
                super(dHtmlWindow, self).LoadFile(val)
            else:
                super(dHtmlWindow, self).SetPage(val)


    def _getVerticalScroll(self):
        return self._verticalScroll

    def _setVerticalScroll(self, val):
        self._verticalScroll = val
        self.EnableScrolling(self._horizontalScroll, self._verticalScroll)
        rt = self.GetScrollPixelsPerUnit()
        self.SetScrollRate(rt[0], {True:rt[1], False:0}[val])


    Children = property(_getChildren, _setChildren, None,
            _("""Child controls of this panel. This excludes the wx-specific
            scroll bars  (list of objects)"""))

    HorizontalScroll = property(_getHorizontalScroll, _setHorizontalScroll, None,
            _("Controls whether this object will scroll horizontally (default=True)  (bool)"))

    Page = property(_getPage, _setPage, None,
            _("URL, file path, or html text of the current page being displayed (default='')  (string)"))

    VerticalScroll = property(_getVerticalScroll, _setVerticalScroll, None,
            _("Controls whether this object will scroll vertically (default=True)  (bool)"))


    DynamicHorizontalScroll = makeDynamicProperty(HorizontalScroll)
    DynamicVerticalScroll = makeDynamicProperty(VerticalScroll)

class _dHtmlWindow_test(dHtmlWindow):
    def afterInit(self):
        self.SetScrollbars(10,10,100,100)
        self.Page = "http://dabodev.com/"

    def onMouseLeftDown(self, evt):
        print "mousedown"
        self.SetFocusIgnoringChildren()

    def onPaint(self, evt):
        print "paint"

    def onKeyDown(self, evt):
        print evt.EventData["keyCode"]

class _dHtmlWindow_test2(dHtmlWindow):
    def afterInit(self):
        self.SetScrollbars(10,10,100,100)
        self.Page = self.PageData()

    def PageData(self):
        return """<html>
        <body bgcolor="#ACAA60">
        <center><table bgcolor="#455481" width="100%" cellspacing="0" cellpadding="0" border="1">
        <tr>
            <td align="center"><h1>dHtmlWindow</h1></td>
        </tr>
        </table>
        </center>
        <p><b>dHtmlWindow</b> is a Dabo UI widget object that wraps a WxPython
        html window.  The widget is designed to display html text.  Be careful
        though, because the widget doesn't support advanced functions like Javascript
        parsing.
        </p>

        <p><b>Dabo</b> is brought to you by <b>Ed Leafe</b>, <b>Paul Mcnett</b>,
        and others in the open source community, Copyright &copy; 2006.
        </p>
        </body>
        </html>
        """

    def onMouseLeftDown(self, evt):
        print "mousedown"
        self.SetFocusIgnoringChildren()

    def onPaint(self, evt):
        print "paint"

    def onKeyDown(self, evt):
        print evt.EventData["keyCode"]



if __name__ == "__main__":
	import test
	test.Test().runTest(_dHtmlWindow_test2)
	test.Test().runTest(_dHtmlWindow_test)

