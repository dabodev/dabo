import gettext, os
import dabo
from dabo.__version__ import version

__domain = "dabo"
__localedir = "locale"

def __translation(domain, version=None, dirs=[]):
	""" Try to find 
	"""
	dirs = [os.path.join(d, __localedir) for d in dirs]
	dirs.append(None) # tell to search in system dirs also
	domains = [domain]
	version and domains.insert(0, "-".join([domain, version]))

	for domain in domains:
		for dir in dirs:
			try:
				return gettext.translation(domain, localedir=dir)
			except IOError:
				pass
	return None

# set default Dabo translation. File is searched under cwd()/locale/$LANG/LC_MESSAGES
# and in system default places.
__trans = __translation(__domain, version["version"], ["."]) or gettext.NullTranslations()

__app_initialized = False

def __add_apptrans():
	global __trans
	try:
		app = dabo.dAppRef
	except AttributeError:
		app = None
	if app:
		appname, appver = [app.getAppInfo(k) for k in ("appName", "appVersion")]
		if appname:
			appname = appname.lower()
			apptrans = __translation(appname, appver, [app.HomeDirectory])
			if apptrans:
				apptrans.add_fallback(__trans)
				__trans = apptrans
				__app_initialized = True

def _(s):
	""" Default localization service. Translation is based on default
	gettext interface. Translation is returned in Unicode.

	Messages are searched first in application translations and in Dabo ones after.
	
	Translation files are searched in
	application.HomeDirectory/locale and system default locale
	directories accoding to gettext conventions(files must be
	placed under ${LANG}/LC_MESSAGES subdirectory. File basename must
	be appName or appName-appVersion in lower case.
	
	Default appName is "dabo".
	"""
	# application initialized, try to install messages
	if not __app_initialized:
		__add_apptrans()	
	return __trans.ugettext(str(s))

	
def n_(s):
	""" Use it if you want to tell translation service about string
	but don't want to translate it inplace.
	"""
	return s

