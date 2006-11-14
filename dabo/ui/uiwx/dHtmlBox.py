import wx.html
import os
import re
import types
import urllib2
import dabo
from dabo.dLocalize import _

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
from dabo.ui import makeDynamicProperty

class dHtmlBox(wx.html.HtmlWindow, cm.dControlMixin):
	"""Creates a scrolled panel that can load and display html pages

	The Html Window can load any html text, file, or url that is fed to it.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._horizontalScroll = self._verticalScroll = True
		self._baseClass = dHtmlBox
		preClass = wx.html.PreHtmlWindow
		if "style" not in kwargs:
			kwargs["style"] = wx.TAB_TRAVERSAL
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
		self.SetScrollRate(10, 10)
		self._source = self._page = ""
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
	
	
	def setImageURLs(self, val):
		"""Replace standard image file names with 'file:///img.pth' references"""
		pat = re.compile(r"""<img (.*)\bsrc=(['"]?)([^'">]+)(['"]?)([^>]*)>""")
		ret = ""
		while True:
			mtch = pat.search(val)
			if mtch:
				beg, end = mtch.span()
				befSrc, qt1, src, qt2, aftSrc = mtch.groups()
				if "file://" in src:
					url = src
				else:
					url = dabo.ui.getImagePath(src, True)
					if url is None:
						# Use the original
						url = src
				ret = ret + val[:beg] + "<img %(befSrc)ssrc=%(qt1)s%(url)s%(qt2)s%(aftSrc)s>" % locals()
				val = val[end:]
			else:
				# No match; add the remaining val to ret
				ret += val
				break
		return ret			


	def _getChildren(self):
		ret = super(dHtmlBox, self)._getChildren()
		return [kid for kid in ret
				if isinstance(kid, dabo.ui.dPemMixinBase.dPemMixinBase)]

	def _setChildren(self, val):
		super(dHtmlBox, self)._setChildren(val)


	def _getHorizontalScroll(self):
		return self._horizontalScroll

	def _setHorizontalScroll(self, val):
		self._horizontalScroll = val
		self.EnableScrolling(self._horizontalScroll, self._verticalScroll)
		rt = self.GetScrollPixelsPerUnit()
		self.SetScrollRate({True:rt[0], False:0}[val], rt[1])


	def _getPage(self):
		return self._page

	def _setPage(self, val):
		if isinstance(val, types.StringTypes):
			try:
				if os.path.exists(val):
					file = open(val, 'r')
					self._source = file.read()
					self.LoadFile(val)
					self._page = val
					return
				elif not val[:7] == "http://":
					val = "http://" + val

				url = urllib2.urlopen(val)
				self._source = url.read()
				self.LoadPage(val)
				self._page = val
			except:
				self._source = "<html><body>Cannot Open URL %s</body><html>" % (val,)
				self._page = ""
				self.SetPage(self._source)


	def _getSource(self):
		return self._source

	def _setSource(self, val):
		if isinstance(val, types.StringTypes):
			val = self.setImageURLs(val)
			self._source = val
			self._page = ""
			self.SetPage(val)


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
			_("URL or file path of the current page being displayed. (default='')  (string)"))

	Source = property(_getSource, _setSource, None,
			_("Html source of the current page being display. (default='')  (string)"))

	VerticalScroll = property(_getVerticalScroll, _setVerticalScroll, None,
			_("Controls whether this object will scroll vertically (default=True)  (bool)"))


	DynamicHorizontalScroll = makeDynamicProperty(HorizontalScroll)
	DynamicVerticalScroll = makeDynamicProperty(VerticalScroll)



class _dHtmlBox_test(dHtmlBox):
	def initProperties(self):
		self.Size = (300,200)

	def afterInit(self):
		self.SetScrollbars(10,10,100,100)
	##		self.Page = "http://dabodev.com/"
		self.Source = self.PageData()

	def PageData(self):
		return """<html>
		<body bgcolor="#ACAA60">
		<center><table bgcolor="#455481" width="100%" cellspacing="0" cellpadding="0" border="1">
		<tr>
			<td align="center"><h1>dHtmlBox</h1></td>
		</tr>
		</table>
		</center>
		<p><b>dHtmlBox</b> is a Dabo UI widget object that wraps a WxPython
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
	test.Test().runTest(_dHtmlBox_test)

