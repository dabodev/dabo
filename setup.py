import os
import glob
import ez_setup # From http://peak.telecommunity.com/DevCenter/setuptools
ez_setup.use_setuptools()

from setuptools import setup, find_packages
from dabo.__version__ import version

daboVersion = version["version"]

# List the paths under dabo/icon/themes:
iconDir = "dabo/icons/themes"
iconDirs = {}
def getIconSubDir(arg, dirname, fnames):
	if ".svn" not in dirname and "cards" not in dirname.lower() and dirname[-1] != "\\":
		icons = glob.glob(os.path.join(dirname, "*.png"))
		if icons:
			subdir = os.path.join(iconDir, dirname[len(arg)+1:])
			subdir = subdir.replace(os.sep, ".")
			iconDirs[subdir] = ["*.png"]
os.path.walk(iconDir, getIconSubDir, iconDir)

package_data = {
		'':['ANNOUNCE', 'AUTHORS', 'ChangeLog', 'INSTALL',
		'LICENSE.TXT', 'README', 'TODO'],
		'dabo.icons': ['*.png', '*.ico'],
		'dabo.icons.cards.small': ['*.png', '*.ico'],
		'dabo.icons.cards.large': ['*.png', '*.ico'],
		'dabo.lib.reporting':['*.rfxml'],
		'dabo.lib.reporting_stefano':['*.rfxml'],
		'dabo.ui.uiwx.macImageProblem':['*.png'],
		'dabo.ui.uiwx.masked':['README'],
		}

package_data.update(iconDirs)


setup(
		name = "Dabo",
		version = daboVersion,
		url = 'http://dabodev.com/',
		author = 'Ed Leafe and Paul McNett',
		author_email = 'dev@dabodev.com',
		description = 'Dabo 3-tier Application Framework',
		license = 'MIT',
		packages = find_packages(),
		package_data = package_data,
)
