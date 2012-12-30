# -*- coding: utf-8 -*-
import wx
import dabo
from dabo.lib.utils import ustr
import dabo.ui

dabo.ui.loadUI("wx")

daboNames = dir(dabo.ui)

dabo_to_wx = {}
wx_to_dabo = {}

for daboName in daboNames:
	daboClass = getattr(dabo.ui, daboName)
	if hasattr(daboClass, "__mro__"):
		for mro in daboClass.__mro__:
			if "<class 'wx." in ustr(mro):
				if "wx._" in ustr(mro):
					# normal wx class: don't include the wx._controls. cruft
					dabo_to_wx[daboName] = "wx.%s" % ustr(mro).split(".")[-1][:-2]
				else:
					# extra class: give the full story:
					dabo_to_wx[daboName] = ustr(mro)[8:-2]
				break

daboNames = dabo_to_wx.items()
daboNames.sort()

for k,v in dabo_to_wx.iteritems():
	wxClasses = wx_to_dabo.setdefault(v, [])
	wxClasses.append(k)

#wxNames = dict([[v,k] for k,v in dabo_to_wx.iteritems()]).items()
wxNames = wx_to_dabo.items()
wxNames.sort()

for eachItem in daboNames:
	print "%s = %s" % (eachItem[0], eachItem[1])

print "\n\n"

for eachItem in wxNames:
	print "%s = %s" % (eachItem[0], ", ".join(eachItem[1]))
