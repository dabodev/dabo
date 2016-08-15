import os
import glob
from setuptools import setup, find_packages
from setuptools.command.sdist import sdist as _sdist

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

# locale dirs:
localeDir = os.path.join(setupDir, "dabo", "locale")
localeDirs = []
def getLocaleDirs(arg, dirname, fnames):
	if dirname[-1] != "\\":
		po_files = tuple(glob.glob(os.path.join(dirname, "*.po")))
		mo_files = tuple(glob.glob(os.path.join(dirname, "*.mo")))
		if po_files:
			subdir = os.path.join(localeDir, dirname[len(arg)+1:])
			localeDirs.append((subdir, ["*.po"]))
		if mo_files:
			subdir = os.path.join(localeDir, dirname[len(arg)+1:])
			localeDirs.append((subdir, ["*.po"]))
os.path.walk(localeDir, getLocaleDirs, localeDir)

package_data = {
	"":["ANNOUNCE", "AUTHORS", "ChangeLog", "INSTALL",
	"LICENSE.TXT", "README", "TODO"],
	"dabo.icons": ["*.png", "*.ico"],
	"dabo.icons.cards.small": ["*.png", "*.ico"],
	"dabo.icons.cards.large": ["*.png", "*.ico"],
	"dabo.lib.reporting":["*.rfxml"],
	"dabo.lib.reporting_stefano":["*.rfxml"],
	"dabo.ui.uiwx.macImageProblem":["*.png"],
	"dabo.ui.uiwx.masked":["README"],
	}

package_data.update(iconDirs)
package_data.update(localeDirs)

version = __version__
setup(
	name = "Dabo",
	version = version,
	url = "http://dabodev.com/",
	download_url = "https://github.com/dabodev/dabo/archive/v%s.zip" % version,
	author = "Ed Leafe and Paul McNett",
	author_email = "dev@dabodev.com",
	description = "Dabo 3-tier Application Framework",
	license = "MIT",
	packages = find_packages(),
	package_data = package_data,
	include_package_data = True,
)
