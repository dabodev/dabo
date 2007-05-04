# -*- coding: utf-8 -*-
import wx.html
import os
import re
import types
import urllib2
import urlparse
import datetime
import dabo
from dabo.dLocalize import _
import dabo.dEvents as dEvents
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlMixin as cm
from dabo.ui import makeDynamicProperty


class dHtmlBox(cm.dControlMixin, wx.html.HtmlWindow):
	"""Creates a scrolled panel that can load and display html pages

	The Html Window can load any html text, file, or url that is fed to it.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._horizontalScroll = self._verticalScroll = True
		self._baseClass = dHtmlBox
		preClass = wx.html.PreHtmlWindow
		if "style" not in kwargs:
			kwargs["style"] = wx.TAB_TRAVERSAL
		self._source = self._page = ""
		self._respondToLinks = True
		cm.dControlMixin.__init__(self, preClass, parent, properties, attProperties, 
				*args, **kwargs)
		self.SetScrollRate(10, 10)
		self.Bind(wx.html.EVT_HTML_LINK_CLICKED, self.__onWxLinkClicked)
		self.bindEvent(dEvents.HtmlLinkClicked, self.__onLinkClicked)


	def __onWxLinkClicked(self, evt):
		self.raiseEvent(dEvents.HtmlLinkClicked, href=evt.GetLinkInfo().GetHref())


	def __onLinkClicked(self, evt):
		if self.RespondToLinks:
			self.Page = evt.href


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
		if isinstance(val, basestring):
			try:
				if os.path.exists(val):
					file = open(val, "r")
					self._source = file.read()
					self.LoadFile(val)
					self._page = val
					return
				elif not val.startswith("http://"):
					# See if the current page starts with it
					if self._page.startswith("http://"):
						# Join it to the current URL
						val = urlparse.urljoin(self._page, val)
					else:
						# Assume that it's an HTTP request
						val = "http://" + val
				url = urllib2.urlopen(val)
				self._source = url.read()
				self.LoadPage(val)
				self._page = val
			except:
				self._source = "<html><body>Cannot Open URL %s</body><html>" % (val,)
				self._page = ""
				self.SetPage(self._source)


	def _getRespondToLinks(self):
		return self._respondToLinks

	def _setRespondToLinks(self, val):
		self._respondToLinks = val
		

	def _getSource(self):
		return self._source

	def _setSource(self, val):
		if isinstance(val, types.StringTypes):
			self._source = val
			self._page = ""
			val = self.setImageURLs(val)
			self.SetPage(val)


	def _getVerticalScroll(self):
		return self._verticalScroll

	def _setVerticalScroll(self, val):
		self._verticalScroll = val
		self.EnableScrolling(self._horizontalScroll, self._verticalScroll)
		rt = self.GetScrollPixelsPerUnit()
		self.SetScrollRate(rt[0], {True:rt[1], False:0}[val])


	HorizontalScroll = property(_getHorizontalScroll, _setHorizontalScroll, None,
			_("Controls whether this object will scroll horizontally (default=True)  (bool)"))

	Page = property(_getPage, _setPage, None,
			_("URL or file path of the current page being displayed. (default='')  (string)"))

	RespondToLinks = property(_getRespondToLinks, _setRespondToLinks, None,
			_("When True (default), clicking a link will attempt to load that linked page.  (bool)"))

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
		self.Source = self.PageData()
		
	
	def PageData(self):
		return """<html>
		<body bgcolor="#ACAA60">
		<center>
			<table bgcolor="#455481" width="100%%" cellspacing="0" cellpadding="0" 
					border="1">
				<tr>
					<td align="center"><h1>dHtmlBox</h1></td>
				</tr>
			</table>
		</center>
		<p><b><font size="160%%" color="#FFFFFF">dHtmlBox</font></b> is a Dabo UI widget that is designed to display html text. 
		Be careful, though, because the widget doesn't support advanced functions like 
		Javascript parsing.</p>
		<p>It's better to think of it as a way to display <b>rich text</b> using 
		<font size="+1" color="#993300">HTML markup</font>, rather
		than a web browser replacement.</p>
		
		<p>&nbsp;</p>
		<div align="center"><img src="daboIcon.ico"></div>

		<p align="center"><b><a href="http://dabodev.com">Dabo</a></b> is brought to you by <b>Ed Leafe</b>, <b>Paul McNett</b>,
		and others in the open source community. Copyright &copy; 2004-%s
		</p>
		</body>
		</html>
		""" % datetime.date.today().year

	def onMouseLeftDown(self, evt):
		print "mousedown"
		self.SetFocusIgnoringChildren()

	def onKeyDown(self, evt):
		print "Key Code:", evt.EventData["keyCode"]



if __name__ == "__main__":
	import test
	test.Test().runTest(_dHtmlBox_test)

