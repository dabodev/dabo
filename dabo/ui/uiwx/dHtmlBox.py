import wx.html 
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


class dHtmlBox(wx.html.HtmlWindow, dcm.dControlMixin):
	"""Creates a control that can display HTML."""
	def __init__(self, parent, properties=None, attProperties=None,
			*args, **kwargs):
		self._baseClass = dHtmlBox
		preClass = wx.html.HtmlWindow

		dcm.dControlMixin.__init__(self, preClass, parent, properties, 
				attProperties, *args, **kwargs)
		

	def _getHtml(self):
		return self.ToText()

	def _setHtml(self, val):
		if self._constructed():
			self.SetPage(val)
		else:
			self._properties["HTML"] = val


	HTML = property(_getHtml, _setHtml, None,
			_("Text displayed in the control  (str)"))
	



class _dHtmlBox_test(dHtmlBox):
	def afterInit(self):
		self.HTML = """
<h1>This is a headline</h1>
<p>This text is <b>bold</b>, <i>italic</i> and <font color="#FF0000">red</font>.</p>
"""


if __name__ == "__main__":
	import test
	test.Test().runTest(_dHtmlBox_test)
