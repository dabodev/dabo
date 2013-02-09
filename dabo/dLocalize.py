#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gettext
import locale
import os
import sys
import warnings

import dabo


_defaultLanguage, _defaultEncoding = locale.getdefaultlocale()

if _defaultLanguage is None:
	_defaultLanguage = dabo.defaultLanguage

if dabo.overrideLocaleLanguage:
	_defaultLanguage = dabo.defaultLanguage

if _defaultEncoding is None:
	_defaultEncoding = dabo.getEncoding()

_domains = {}
_currentTrans = None

_languageAliases = {
		"catalan": "ca", "català":"ca",
		"german": "de", "deutsch": "de",
		"greek": "el", "ελληνικά":"el",
		"english": "en", "english_united states":"en",
		"english (uk)": "en_gb", "english_uk":"en_gb", "english_great britain":"en_gb",
		"finnish": "fi", "suomi":"fi",
		"french": "fr", "francais": "fr", "français": "fr",
		"hindi": "hi",
		"hungarian": "hu", "magyar":"hu", "mɒɟɒr": "hu",
		"indonesian": "id", "bahasa indonesia":"id",
		"italian": "it", "italiano": "it",
		"japanese": "ja", "日本語": "ja", "nihoŋɡo": "ja",
		"latvian": "lv", "lettish": "lv", "latviešu valoda": "lv",
		"dutch": "nl", "nederlands":"nl",
		"occitan": "oc", "provençal":"oc",
		"polish": "pl", "polszczyzna":"pl", "język polski":"pl",
		"portuguese": "pt", "portuguêse": "pt",
		"portuguese (brazilian)": "pt_br", "português brasileiro": "pt_br",
		"romanian": "ro", "română":"ro",
		"russian": "ru", "русский язык": "ru", "russkiy yazyk": "ru",
		"spanish": "es", "espanol":"es", "español":"es",
		"swedish": "sv", "svenska":"sv",
		"thai": "th", "ภาษาไทย":"th", "phasa thai": "th",
		"chinese (simplified)": "zh_cn", "汉语":"zh_cn", "华语":"zh_cn",
		}


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
	"""Change the language that strings get translated to, for all installed domains.
	NOTE: rather than call the install() method of the gettext.translation objects,
	which would globally bind the '_' name, we'll just set the '_currentTrans'
	name to the translation object.
	"""
	from dabo.lib.utils import ustr
	global _domains, _currentTrans
	lang = _languageAliases.get(lang.lower(), lang)

	if lang is not None and isinstance(lang, basestring):
		lang = [lang]

	daboTranslation = None
	daboLocaleDir = _domains.get("dabo", None)
	if daboLocaleDir:
		try:
			daboTranslation = gettext.translation("dabo", daboLocaleDir, languages=lang, codeset=charset)
		except IOError:
			# No translation file found
			dabo.log.error("""
No translation file found for domain 'dabo'.
    Locale dir = %s
    Languages = %s
    Codeset = %s """ % (daboLocaleDir, ustr(lang), charset))
			# Default to US English
			daboTranslation = gettext.translation("dabo", daboLocaleDir, languages=["en"], codeset=charset)
		_currentTrans = daboTranslation.ugettext

	for domain, localedir in _domains.items():
		if domain == "dabo":
			continue  ## already handled separately above
		try:
			translation = gettext.translation(domain, localedir, languages=lang, codeset=charset)
		except IOError:
			dabo.log.error("No translation found for domain '%s' and language %s." % (domain, lang))
			dabo.log.error("""
No translation file found for domain '%s'.
    Locale dir = %s
    Languages = %s
    Codeset = %s """ % (domain, daboLocaleDir, ustr(lang), charset))
		if daboTranslation:
			translation.add_fallback(daboTranslation)
		_currentTrans = translation.ugettext


def getDaboLocaleDir():
	localeDirNames = ("dabo.locale", "locale")
	localeDirRoots = [os.path.split(dabo.__file__)[0]] + sys.path
	for localeDirRoot in localeDirRoots:
		for localeDirName in localeDirNames:
			localeDir = os.path.join(localeDirRoot, localeDirName)
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
			if os.path.isdir(localeDir):
				break
		if os.path.isdir(localeDir):
			break
	return localeDir


if __name__ == "__main__":
	install()
	print
	print "sys.getdefaultencoding():", sys.getdefaultencoding()
	if dabo.loadUserLocale:
		locale.setlocale(locale.LC_ALL, '')
		print "locale.getlocale():", locale.getlocale()
	else:
		print "locale.getdefaultlocale():", locale.getdefaultlocale()
	print "_defaultLanguage, _defaultEncoding:", _defaultLanguage, _defaultEncoding
	print

	stringsToTranslate = ("OK", "&File", "&Edit", "&Help", "Application finished.")
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

