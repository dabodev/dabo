# -*- coding: utf-8 -*-

import sys
import locale

# Do this up here, because we may be changing sys.getdefaultencoding:
defLang, defCharset = locale.getlocale()  ## need to respect this, if set, IIUC
if defLang is None:
	defLang = locale.getdefaultlocale()[0]
	if defLang is None:
		defLang = "en"

if defCharset is None:
	defCharset = sys.getfilesystemencoding()
	if defCharset is None:
		defCharset = "utf-8"

reload(sys)
sys.setdefaultencoding(defCharset)

import os
import gettext
import dabo


_appInitialized = False
_appHasLocale = False
_daboTranslate = None
_appTranslate = None
_localeDir = "locale"
_frozenLocaleDir = "dabo.locale"

languageAliases = {"english": "en",
		"spanish": "es", "espanol": "es", "español": "es",
		"french": "fr", "francais": "fr", "français": "fr", 
		"german": "de", "deutsch": "de",
		"italian": "it", "italiano": "it", 
		"portuguese": "pt", "portuguése": "pt",
		"russian": "ru"}

def _(s):
	"""Translate the passed string into the current language, if possible.   

	Dabo provides translations of common strings into several languages. If a 
	translation is found for the passed string, it will be returned. Otherwise,
	the identical string will be returned.

	In addition, user applications can define their own translations, in which
	case we'll first look for translations in the application's locale directory,
	and then fall back on Dabo's translations.
 
	Localization files of app should be in under its locale directory, with the .mo
	file's named after the application's short name. The default application name
	is "daboapplication", so by default the app's .mo files should be named
	"daboapplication.mo". 
	"""
	global defLang, _appInitialized, _appHasLocale
	
	if not _appInitialized:
		try:
			app = dabo.dAppRef
		except AttributeError:
			app = None
			
		if app:
			_appInitialized = True
			# If appShortName not changed in user app, defaults to "daboapplication"
			appName = app.getAppInfo("appShortName")
			if appName is not None:
				_appHasLocale = setLanguage(domain=appName.lower().replace(" ", "_"),
						localedir=os.path.join(app.HomeDirectory, _localeDir))


	# Always return Unicode strings
	if _appInitialized and _appHasLocale:
		# Use app's localization, with Dabo's as a fallback:
		return _appTranslate.ugettext(s)
	else:
		# App's localization is not in place; use only Dabo's:
		return _daboTranslate.ugettext(s)
		

def n_(s):
	""" Use it if you want to tell translation service about string
	but don't want to translate it inplace.
	"""
	return s
	#TODO: wouldn't it be better, if we will use something like _("string",False) in _ function ??? 
	# i.e. one more argument for _function, telling by default to translate strings ?
	# def _(s, translate=True):
	#  pkm: Agree. Actually, can someone give an example of when you'd even want this?
	#	   Do we use it even?


def setLanguage(lang=None, charset=None, domain="dabo", localedir=None):
	"""Use it if you want to switch to another localizations than your default.
	You should call it twice - once for dabo framework, and once for app.
	"""
	global defLang, defCharset, _daboTranslate, _appTranslate
	
	#TODO: we should search system localizations directory as well

	if localedir is None:
		localedir = os.path.join(os.path.split(dabo.__file__)[0], _localeDir)
		if not os.path.exists(localedir):
			# Frozen app?
			# First need to find the directory that contains the .exe:
			startupDir = localeDir
			while startupDir:
				startupDir = os.path.split(startupDir)[0]
				if os.path.isdir(startupDir):
					break
			if domain == "dabo":
				frozenLocaleDir = _frozenLocaleDir
			else:
				frozenLocaleDir = _localeDir
			localedir = os.path.join(startupDir, frozenLocaleDir)

	if charset is None:
		charset = defCharset

	if lang is None:
		lang = defLang
	else:
		lang = lang.lower()
		# It might be the full name instead of the two-letter abbreviation:
		lang = languageAliases.get(lang, lang)
		
	localefile = gettext.find(domain, localedir, languages=[lang], all=True)

	if domain == "dabo":
		if not localefile:
			raise IOError, "No translation files found for Dabo. Looked in %s." % localedir
		_daboTranslate = gettext.translation(domain, localedir, languages=[lang], codeset=charset)
		defLang = lang
	else:
		if localefile:
			_appTranslate = gettext.translation(domain, localedir, languages=[lang], codeset=charset)
			if _appTranslate:
				_appTranslate.add_fallback(_daboTranslate)
			return bool(_appTranslate)
		return False
		

defLang, defCharset = ("en", "utf-8")
#defLang, defCharset = locale.getdefaultlocale()

#if defLang is None:
#	defLang = "en"
#else:
#	defLang = defLang[:2]
#if defCharset is None:
#	defCharset = "UTF-8"

setLanguage(domain="dabo")

if __name__ == "__main__":
	print "user default locale:", locale.getdefaultlocale()
	print "framework locale:", defLang, defCharset

	for lan in ("en", "es"):
		setLanguage(lan)
		print "%s:" % lan, _("Framework localization test")

