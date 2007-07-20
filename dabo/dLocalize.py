# -*- coding: utf-8 -*-
import gettext
import locale
import os
import re
import dabo


def getLanguages():
	# Probably need to add more
	langs = gettext.find("dabo", daboLocaleDir, languages=_trans.keys(), all=True)
	sep = os.path.sep
	
	ret = []
	for lang in langs:
		pathparts = lang.split(sep)
		pos = pathparts.index("locale")
		ret.append(pathparts[pos+1])
	return ret


def setLanguage(lang=None, charset=None):
	global defLang, defCharset, _trans
	if charset is None:
		charset = defCharset
	if lang is None:
		lang = defLang
	else:
		lang = lang.lower()
		# It might be the full name instead of the two-letter abbreviation
		if lang not in getLanguages():
			try:
				lang = {"english": "en", 
						"spanish": "es", "espanol": "es", "español": "es",
						"french": "fr", "francais": "fr", "français": "fr", 
						"german": "de", "deutsch": "de", 
						"italian": "it", "italiano": "it", 
						"portuguese": "pt", "portuguése": "pt",
						"russian": "ru"}[lang]
			except KeyError:
				pass
	if not lang in getLanguages():
		raise IOError, "Invalid language '%s'" % lang
	
	if _trans.get(lang) is None:
		_trans[lang] = gettext.translation("dabo", daboLocaleDir, 
				languages=[lang], codeset=charset)
	defLang = lang
	
	
def _(s):
	global defLang, _trans
	return _trans[defLang].gettext(s)
	

def n_(s):
	""" Use it if you want to tell translation service about string
	but don't want to translate it inplace.
	"""
	global defLang
	return _trans[defLang].gettext(s)


daboLocaleDir = os.path.join(os.path.split(dabo.__file__)[0], "locale")
_trans = {"en": None, "fr": None, "es": None, "pt": None, "ru": None, "de": None, "it": None}
defLang, defCharset = locale.getlocale()
if defLang is None:
	defLang = "en"
else:
	defLang = defLang[:2]
if defCharset is None:
	defCharset = "ISO8859-1"
setLanguage()
