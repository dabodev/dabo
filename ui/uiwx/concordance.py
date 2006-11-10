import wx
import dabo

dabo.ui.loadUI("wx")

daboNames = dir(dabo.ui)

dabo_to_wx = {}
wx_to_dabo = {}

for daboName in daboNames:
	daboClass = getattr(dabo.ui, daboName)
	if hasattr(daboClass, "__mro__"):
		for mro in daboClass.__mro__:
			if "<class 'wx." in str(mro):
				try:
					if "wx._" in str(mro):
						# normal wx class: don't include the wx._controls. cruft
						dabo_to_wx[daboName] = "wx.%s" % str(mro).split(".")[-1][:-2]
					else:
						# extra class: give the full story:
						dabo_to_wx[daboName] = str(mro)[8:-2] 
				except:
					pass
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
