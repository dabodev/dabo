# -*- coding: utf-8 -*-

import sys
import os
import locale
import gettext
import warnings
import dabo


_defaultLanguage, _defaultEncoding = locale.getdefaultlocale()

if _defaultLanguage is None:
	_defaultLanguage = dabo.settings.defaultLanguage

if _defaultEncoding is None:
	_defaultEncoding = dabo.settings.defaultEncoding


_domains = {}
_currentTrans = None

_languageAliases = {"english": "en", "English_United States":"en",
		"spanish": "es", "espanol": "es", "español": "es",
		"french": "fr", "francais": "fr", "français": "fr", 
		"german": "de", "deutsch": "de",
		"italian": "it", "italiano": "it", 
		"portuguese": "pt", "portuguése": "pt",
		"russian": "ru"}

def _(s):
	"""Return the localized translation of s, or s if translation not possible."""
	try:
		return _currentTrans(s)
	except TypeError:
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
			raise ValueError("Must send your application's localedir explicitly.")
		localedir = getDaboLocaleDir()
	_domains[domain] = localedir
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
		try:
			daboTranslation = gettext.translation("dabo", daboLocaleDir, languages=lang, codeset=charset)
			_currentTrans = daboTranslation.ugettext
		except IOError:
			# No translation file found
			dabo.errorLog.write("""
No translation file found for domain 'dabo'.
    Locale dir = %s
    Languages = %s
    Codeset = %s """ % (daboLocaleDir, str(lang), charset))

	for domain, localedir in _domains.items():
		if domain == "dabo":
			continue  ## already handled separately above
		try:
			translation = gettext.translation(domain, localedir, languages=lang, codeset=charset)
		except IOError:
			dabo.errorLog.write("No translation found for domain '%s' and language %s." % (domain, lang))
			dabo.errorLog.write("""
No translation file found for domain '%s'.
    Locale dir = %s
    Languages = %s
    Codeset = %s """ % (domain, daboLocaleDir, str(lang), charset))
		if daboTranslation:
			translation.add_fallback(daboTranslation)
		_currentTrans = translation.ugettext


def getDaboLocaleDir():
	localeDirNames = ("dabo.locale", "locale")
	for localeDirName in localeDirNames:
		localeDir = os.path.join(os.path.split(dabo.__file__)[0], localeDirName)
		if not os.path.isdir(localeDir):
			# Frozen app?
			# First need to find the directory that contains the executable. On the Mac,
			# it might be a directory at a lower level than dabo itself.
			startupDir = localeDir
			while startupDir:
				newDir = os.path.split(startupDir)[0]
				if newDir == startupDir:
					# At the root dir
					break
				startupDir = newDir
				candidate = os.path.join(startupDir, localeDirName)
				if os.path.isdir(candidate):
					break
			if os.path.isdir(candidate):
				localeDir = candidate
				break
	return localeDir


if __name__ == "__main__":

	install()

	print
	print "sys.getdefaultencoding():", sys.getdefaultencoding()
	if dabo.settings.loadUserLocale:
		locale.setlocale(locale.LC_ALL, '')
		print "locale.getlocale():", locale.getlocale()
	else:
		print "locale.getdefaultlocale():", locale.getdefaultlocale()
	print "_defaultLanguage, _defaultEncoding:", _defaultLanguage, _defaultEncoding
	print

	stringsToTranslate = ("&File", "&Edit", "&Help", "Application finished.")
	max_len = {}
	for s in stringsToTranslate:
		max_len[s] = len(s)
	translatedStrings = []
	for lang in sorted(set(_languageAliases.values()) - set(("en",))):
		translatedStringsLine = [lang]
		setLanguage(lang)
		for s in stringsToTranslate:
			translated = _(s)
			translatedStringsLine.append(translated)
			max_len[s] = max(max_len[s], len(translated))
		translatedStrings.append(tuple(translatedStringsLine))

	def line(strings=None):
		lin = []
		add = lin.append
		if strings is None:
			# print the boundary
			add("+----")
			for s in stringsToTranslate:
				add("+-%s-" % ("-" * max_len[s]))
			add("+")
		else:
			# print the text
			for i, s in enumerate(strings):
				len_s = max_len.get(i and stringsToTranslate[i-1], len(s))
				add("| %s " % s.ljust(len_s))
			add("|")
		return ''.join(lin)

	print line()
	print line(("en",) + stringsToTranslate)
	print line()
	for l in translatedStrings:
		setLanguage(l[0])
		print line(l)
	print line()
	
