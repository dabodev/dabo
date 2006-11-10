import wx
import dabo

dabo.ui.loadUI("wx")

daboNames = dir(dabo.ui)
wxNames = dir(wx)

dabo_to_wx = {}

for daboName in daboNames:
	daboClass = getattr(dabo.ui, daboName)
	if hasattr(daboClass, "__mro__"):
		for mro in daboClass.__mro__:
			if "<class 'wx." in str(mro):
				try:
					dabo_to_wx[daboName] = "wx.%s" % str(mro).split(".")[-1][:-2]
				except:
					pass
				break

daboNames = dabo_to_wx.items()
daboNames.sort()

wxNames = dict([[v,k] for k,v in dabo_to_wx.iteritems()]).items()
wxNames.sort()

for eachItem in daboNames:
	print "%s = %s" % (eachItem[0], eachItem[1])

print "\n\n"

for eachItem in wxNames:
	print "%s = %s" % (eachItem[0], eachItem[1])
