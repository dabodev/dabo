# -*- coding: utf-8 -*-
import wx.html
import os
import re
import string
import types
import urllib2
import urlparse
import datetime
import dabo
from dabo.dLocalize import _
import dabo.dEvents as dEvents
from dabo.ui import makeDynamicProperty
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlMixin as cm
try:
	import webbrowser as wb
except ImportError:
	wb = None


class dHtmlBox(cm.dControlMixin, wx.html.HtmlWindow):
	"""
	Creates a scrolled panel that can load and display html pages. The Html Window
	can load any html text, file, or url that is fed to it.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._horizontalScroll = self._verticalScroll = True
		self._baseClass = dHtmlBox
		preClass = wx.html.PreHtmlWindow
		if "style" not in kwargs:
			kwargs["style"] = wx.TAB_TRAVERSAL
		self._source = self._page = ""
		self._respondToLinks = True
		self._openLinksInBrowser = False
		cm.dControlMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)
		self.SetScrollRate(10, 10)
		if wx.VERSION >= (2, 7):
			self.Bind(wx.html.EVT_HTML_LINK_CLICKED, self.__onWxLinkClicked)
		else:
			# no such event, so we need to override the OnCellClicked event
			self.OnCellClicked = self.__OnCellClicked


	def _initEvents(self):
		super(dHtmlBox, self)._initEvents()
		self.bindEvent(dEvents.HtmlLinkClicked, self.__onLinkClicked)


	def __OnCellClicked(self, cell, x, y, evt):
		self.raiseEvent(dEvents.HtmlLinkClicked, href=cell.GetLink().GetHref())


	def __onWxLinkClicked(self, evt):
		self.raiseEvent(dEvents.HtmlLinkClicked, href=evt.GetLinkInfo().GetHref())


	def __onLinkClicked(self, evt):
		if self.RespondToLinks:
			if evt.href.startswith("app://") or evt.href.startswith("form://"):
				# query string contains method to call and optional arguments.
				self._processInternalLink(evt.href)
				evt.stop()
			elif wb and self.OpenLinksInBrowser:
				wb.open(evt.href, new=True)
			else:
				# Open in the control itself
				self.Page = evt.href


	def _processInternalLink(self, queryString):
		# Note that all arguments are string
		if queryString.startswith("app://"):
			obj = self.Application
		elif queryString.startswith("form://"):
			obj = self.Form
		else:
			raise ValueError, _("Internal link must resolve to Form or Application.")
		queryString = queryString[queryString.index("//") + 2:]
		try:
			meth, args = queryString.split("?")
			qsargs = args.split("&")
		except ValueError:
			meth = queryString
			qsargs = []
		args = []
		kwargs = {}
		for qsarg in qsargs:
			try:
				name, value = qsarg.split("=", 1)
				kwargs[name] = value
			except ValueError:
				args.append(qsarg)
		getattr(obj, meth)(*args, **kwargs)


	def copy(self):
		"""Implement the plain text version of copying"""
		return self.SelectionToText()


	def setImageURLs(self, val):
		"""Replace standard image file names with 'file:///img.pth' references"""
		pat = re.compile(r"""<img (.*)\bsrc=(['"]?)([^'">]+)(['"]?)([^>]*)>""")
		def repl(match):
			beg, end = match.span()
			befSrc, qt1, src, qt2, aftSrc = match.groups()
			if "file://" in src:
				url = src
			else:
				url = dabo.ui.getImagePath(src, True)
				if url is None:
					# Use the original
					url = src

			if self.Application.Platform == "Win":
				# broken image links if the path contains the drive letter
				pos = url.find(":/", len("file:///"), len(url))
				if pos:
					drive_letter = url[pos-1]
					if drive_letter in string.ascii_letters:
						url = url.replace("%s:/" % drive_letter, "")
			return "<img %(befSrc)ssrc=%(qt1)s%(url)s%(qt2)s%(aftSrc)s>" % locals()
		return pat.sub(repl, val)


	def _getHorizontalScroll(self):
		return self._horizontalScroll

	def _setHorizontalScroll(self, val):
		self._horizontalScroll = val
		self.EnableScrolling(self._horizontalScroll, self._verticalScroll)
		rt = self.GetScrollPixelsPerUnit()
		self.SetScrollRate({True:rt[0], False:0}[val], rt[1])


	def _getOpenLinksInBrowser(self):
		return self._openLinksInBrowser

	def _setOpenLinksInBrowser(self, val):
		if self._constructed():
			self._openLinksInBrowser = val
		else:
			self._properties["OpenLinksInBrowser"] = val


	def _getPage(self):
		return self._page

	def _setPage(self, val):
		if not self._constructed():
			self._properties["Page"] = val
			return
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
			except urllib2.URLError:
				self._source = "<html><body>Cannot Open URL %s</body><html>" % (val,)
				self._page = ""
				self.SetPage(self._source)


	def _getRespondToLinks(self):
		return self._respondToLinks

	def _setRespondToLinks(self, val):
		self._respondToLinks = val


	def _getSelectedText(self):
		return self.SelectionToText()


	def _getSource(self):
		return self._source

	def _setSource(self, val):
		if not self._constructed():
			self._properties["Source"] = val
			return
		if isinstance(val, types.StringTypes):
			self._source = val
			self._page = ""
			val = self.setImageURLs(val)
			self.SetPage(val)


	def _getShowScrollBars(self):
		return not self._hasWindowStyleFlag(wx.html.HW_SCROLLBAR_NEVER)

	def _setShowScrollBars(self, val):
		if bool(val):
			self._delWindowStyleFlag(wx.html.HW_SCROLLBAR_NEVER)
			self._addWindowStyleFlag(wx.html.HW_SCROLLBAR_AUTO)
		else:
			self._delWindowStyleFlag(wx.html.HW_SCROLLBAR_AUTO)
			self._addWindowStyleFlag(wx.html.HW_SCROLLBAR_NEVER)


	def _getText(self):
		return self.ToText()


	def _getVerticalScroll(self):
		return self._verticalScroll

	def _setVerticalScroll(self, val):
		self._verticalScroll = val
		self.EnableScrolling(self._horizontalScroll, self._verticalScroll)
		rt = self.GetScrollPixelsPerUnit()
		self.SetScrollRate(rt[0], {True:rt[1], False:0}[val])

	HorizontalScroll = property(_getHorizontalScroll, _setHorizontalScroll, None,
			_("Controls whether this object will scroll horizontally (default=True)  (bool)"))

	OpenLinksInBrowser = property(_getOpenLinksInBrowser, _setOpenLinksInBrowser, None,
			_("""When True, clicking on an HREF link will open the URL in the default web browser
			instead of in the control itself. Default=False.  (bool)"""))

	Page = property(_getPage, _setPage, None,
			_("URL or file path of the current page being displayed. (default='')  (string)"))

	RespondToLinks = property(_getRespondToLinks, _setRespondToLinks, None,
			_("When True (default), clicking a link will attempt to load that linked page.  (bool)"))

	SelectedText = property(_getSelectedText, None, None,
			_("Currently selected text. Returns the empty string if nothing is selected. Read-only  (str)"))

	ShowScrollBars = property(_getShowScrollBars, _setShowScrollBars, None,
			_("When Tru (default), scrollbars will be shown as needed.  (bool)"))

	Source = property(_getSource, _setSource, None,
			_("Html source of the current page being display. (default='')  (string)"))

	Text = property(_getText, None, None,
			_("""Returns the displayed plain text content of the control, free of any
			HTML markup. Read-only  (str)"""))

	# alias to fall in line with the rest of Dabo.
	Value = Source

	VerticalScroll = property(_getVerticalScroll, _setVerticalScroll, None,
			_("Controls whether this object will scroll vertically (default=True)  (bool)"))


	DynamicHorizontalScroll = makeDynamicProperty(HorizontalScroll)
	DynamicVerticalScroll = makeDynamicProperty(VerticalScroll)
	DynamicSource = makeDynamicProperty(Source)



class _dHtmlBox_test(dHtmlBox):
	def initProperties(self):
		self.BorderWidth = 5
		self.BorderColor = "darkblue"
		self.OpenLinksInBrowser = True
		self.Source = self.getPageData()

	def getPageData(self):
		return """<html>
		<body bgcolor="#B0C4DE">
		<center>
			<table bgcolor="#8470FF" width="100%%" cellspacing="0" cellpadding="0"
					border="1">
				<tr>
					<td align="center"><h1>dHtmlBox</h1></td>
				</tr>
			</table>
		</center>
		<p><b><font size="+2" color="#FFFFFF">dHtmlBox</font></b> is a Dabo UI widget that is designed to display html text.
		Be careful, though, because the widget doesn't support advanced functions like
		Javascript parsing.</p>
		<p>It's better to think of it as a way to display <b>rich text</b> using
		<font size="+1" color="#993300">HTML markup</font>, rather
		than a web browser replacement, although you <i>can</i> create links that will open
		in a web browser, like this: <a href="http://wiki.dabodev.com">Dabo Wiki</a>.</p>

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


def textChangeHandler(evt):
	dabo.ui.callAfter(evt.EventObject.flushValue)

def resetHTML(evt):
	frm = evt.EventObject.Form
	frm.htmlbox.Source = frm.htmlbox.getPageData()
	frm.update()



if __name__ == "__main__":
	from dabo.dApp import dApp
	app = dApp(MainFormClass=None)
	app.setup()
	frm = dabo.ui.dForm()
	pnl = dabo.ui.dPanel(frm)
	frm.Sizer.append1x(pnl)
	sz = pnl.Sizer = dabo.ui.dSizer("v")
	ht = _dHtmlBox_test(pnl, RegID="htmlbox")
	sz.append(ht, 2, "x", border=10)
	lbl = dabo.ui.dLabel(pnl, Caption="Edit the HTML below, then press 'Tab' to update the rendered HTML")
	sz.appendSpacer(5)
	sz.append(lbl, halign="center")
	edt = dabo.ui.dEditBox(pnl, RegID="editbox", DataSource=ht, DataField="Source")
	edt.bindEvent(dEvents.KeyChar, textChangeHandler)
	sz.append1x(edt, border=10)
	btn = dabo.ui.dButton(pnl, Caption="Reset", OnHit=resetHTML)
	sz.append(btn, halign="right", border=10, borderSides=["right", "bottom"])

	frm.show()
	app.start()

