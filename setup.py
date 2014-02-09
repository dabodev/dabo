import os
import glob
import ez_setup # From http://peak.telecommunity.com/DevCenter/setuptools
ez_setup.use_setuptools()

from setuptools import setup, find_packages
from dabo.version import __version__

setupDir = os.path.dirname(__file__)

# List the paths under dabo/icon/themes:
iconDir = os.path.join(setupDir, "dabo", "icons", "themes")
iconDirs = {}
def getIconSubDir(arg, dirname, fnames):
	if "cards" not in dirname.lower() and dirname[-1] != "\\":
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
		version = __version__,
		url = 'http://dabodev.com/',
		download_url = 'https://github.com/dabodev/dabo/archive/v%s.zip' % __version__,
		author = 'Ed Leafe and Paul McNett',
		author_email = 'dev@dabodev.com',
		description = 'Dabo 3-tier Application Framework',
		license = 'MIT',
		packages = find_packages(),
		package_data = package_data,
)
