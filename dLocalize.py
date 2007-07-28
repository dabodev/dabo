# -*- coding: utf-8 -*-
import os
import gettext
import locale
import warnings
import dabo

_domains = {}

_languageAliases = {"english": "en",
		"spanish": "es", "espanol": "es", "español": "es",
		"french": "fr", "francais": "fr", "français": "fr", 
		"german": "de", "deutsch": "de",
		"italian": "it", "italiano": "it", 
		"portuguese": "pt", "portuguése": "pt",
		"russian": "ru"}


def install(domain="dabo", localedir=None, unicode_mo=True):
	"""Install the gettext translation service for the passed domain.

	Either Dabo will be the only domain, or Dabo will be the fallback for a 
  different domain that the user's application set up.
	"""
	global _domains

	if localedir is None:
		if domain != "dabo":
			raise ValueError, "Must send your application's localedir explicitly."
		localedir = getDaboLocaleDir()
	_domains[domain] = localedir
	gettext.install(domain, localedir, unicode=unicode_mo)
	setLanguage()


def isValidDomain(domain, localedir):
	"""Return True if the localedir appears to contain translations for the domain."""
	return bool(gettext.find(domain, localedir, all=True))


def setLanguage(lang=None, charset=None):
	"""Change the language that strings get translated to, for all installed domains."""
	global _domains

	lang = _languageAliases.get(lang, lang)

	if lang is not None and isinstance(lang, basestring):
		lang = [lang]

	daboTranslation = None
	daboLocaleDir = _domains.get("dabo", None)
	if daboLocaleDir:
		daboTranslation = gettext.translation("dabo", daboLocaleDir, languages=lang, codeset=charset)
		daboTranslation.install()

	for domain, localedir in _domains.items():
		if domain == "dabo":
			continue  ## already handled separately above
		try:
			translation = gettext.translation(domain, localedir, languages=lang, codeset=charset)
		except IOError:
			raise IOError, "No translation found for domain '%s' and language %s." % (domain, lang)
		if daboTranslation:
			translation.add_fallback(daboTranslation)
		translation.install()


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


# All kinds of user apps (think appwizard) have the deprecated import of _:
def _(s):
	warnings.warn("Please remove your 'from dLocalize import _' statement.", DeprecationWarning, stacklevel=2)
	__builtins__["_"](s)

def n_(s):
	warnings.warn("Please remove your 'from dLocalize import n_' statement.", DeprecationWarning, stacklevel=2)
	__builtins__["_"](s)


