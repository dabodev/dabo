# -*- coding: utf-8 -*-

import sys
import locale
import os
import gettext
import warnings
import dabo


_defaultLanguage, _defaultEncoding = locale.getlocale()

if _defaultLanguage is None:
	_defaultLanguage = "en"

if _defaultEncoding is None:
	_defaultEncoding = "utf-8"

_domains = {}
_currentTrans = None

_languageAliases = {"english": "en",
		"spanish": "es", "espanol": "es", "español": "es",
		"french": "fr", "francais": "fr", "français": "fr", 
		"german": "de", "deutsch": "de",
		"italian": "it", "italiano": "it", 
		"portuguese": "pt", "portuguése": "pt",
		"russian": "ru"}

def _(s):
	"""Return the localized translation of s, or s if translation not possible."""
	if _currentTrans is not None:
		return _currentTrans(s)
	return s


def n_(s):
	return s


def install(domain="dabo", localedir=None, unicode_mo=True):
	"""Install the gettext translation service for the passed domain.

	Either Dabo will be the only domain, or Dabo will be the fallback for a 
  different domain that the user's application set up.
	"""
	global _domains, _defaultLanguage, _defaultEncoding

	if localedir is None:
		if domain != "dabo":
			raise ValueError, "Must send your application's localedir explicitly."
		localedir = getDaboLocaleDir()
	_domains[domain] = localedir
	#gettext.install(domain, localedir, unicode=unicode_mo)  ## No, don't globally bind _
	setLanguage(_defaultLanguage, _defaultEncoding)


def isValidDomain(domain, localedir):
	"""Return True if the localedir appears to contain translations for the domain."""
	return bool(gettext.find(domain, localedir, all=True))


def setLanguage(lang=None, charset=None):
	"""Change the language that strings get translated to, for all installed domains."""
	global _domains, _currentTrans

	lang = _languageAliases.get(lang, lang)

	if lang is not None and isinstance(lang, basestring):
		lang = [lang]

	daboTranslation = None
	daboLocaleDir = _domains.get("dabo", None)
	if daboLocaleDir:
		daboTranslation = gettext.translation("dabo", daboLocaleDir, languages=lang, codeset=charset)
#		daboTranslation.install()  ## No, don't globally bind _
		_currentTrans = daboTranslation.ugettext

	for domain, localedir in _domains.items():
		if domain == "dabo":
			continue  ## already handled separately above
		try:
			translation = gettext.translation(domain, localedir, languages=lang, codeset=charset)
		except IOError:
			raise IOError, "No translation found for domain '%s' and language %s." % (domain, lang)
		if daboTranslation:
			translation.add_fallback(daboTranslation)
#		translation.install()  ## No, don't globally bind _
		_currentTrans = translation.ugettext


def getDaboLocaleDir():
	localedir = os.path.join(os.path.split(dabo.__file__)[0], "locale")
	if not os.path.isdir(localedir):
		# Frozen app?
		# First need to find the directory that contains the .exe:
		startupDir = localeDir
		while startupDir:
			startupDir = os.path.split(startupDir)[0]
			if os.path.isdir(startupDir):
				break
		localedir = os.path.join(startupDir, "dabo.locale")
	return localedir


if __name__ == "__main__":
	install()
	print "sys.getdefaultencoding():", sys.getdefaultencoding()
	print "locale.getlocale():", locale.getlocale()
	print "_defaultLanguage, _defaultEncoding:", _defaultLanguage, _defaultEncoding
	stringsToTranslate = ("Hey", "Application finished.")
	for lang in set(_languageAliases.values()):
		print "Setting language to '%s'." % (lang)
		setLanguage(lang)
		for s in stringsToTranslate:
			print "Translating '%s':" % s, _(s)

