import ez_setup # From http://peak.telecommunity.com/DevCenter/setuptools
ez_setup.use_setuptools()

from setuptools import setup, find_packages
from dabo.__version__ import version

daboVersion = version["version"]

setup(
		name = "Dabo",
		version = daboVersion,
		url = 'http://dabodev.com/',
		author = 'Ed Leafe and Paul McNett',
		author_email = 'dev@dabodev.com',
		description = 'Dabo 3-tier Application Framework',
		license = 'MIT',
		packages = find_packages(),
		package_data = {
				'':['ANNOUNCE', 'AUTHORS', 'ChangeLog', 'INSTALL',
				'LICENSE.TXT', 'README', 'TODO'],
				'dabo.icons': ['*.png'],
				'dabo.lib.reporting':['*.rfxml'],
				'dabo.lib.reporting_stefano':['*.rfxml'],
				'dabo.ui.uiwx.macImageProblem':['*.png'],
				'dabo.ui.uiwx.masked':['README'],
		},
)
