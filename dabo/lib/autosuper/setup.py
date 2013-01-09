# -*- coding: utf-8 -*-
from distutils.core import setup
from distutils.extension import Extension
import autosuper

params = {
    'name':         'Improved autosuper',
    'version':      '0.9.6',
    'description':  'Use self.super(*p, **kw) instead of super(cls, self).func(*p, **kw)',
    'long_description': autosuper.__doc__,
    'author':       'Tim Delaney',
    'author_email': 'tcdelaney@optusnet.com.au',
    'url':          'http://members.optusnet.com.au/tcdelaney/python.html#autosuper',
    'download_url': 'http://members.optusnet.com.au/tcdelaney/autosuper.zip',
    'license':      'BSD-style',
    'classifiers':  [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development',
    ],
    'py_modules':   ['autosuper'],
}

try:
    # If either Pyrex or a usable compiler is not installed, we still want
    # to install the Python version
    from Pyrex.Distutils import build_ext

    ext = {
      'ext_modules': [Extension('_autosuper', ['_autosuper.pyx']),],
      'cmdclass':    {'build_ext': build_ext}
    }

    pyrex_commands = params.copy()
    pyrex_commands.update(ext)
    setup(**pyrex_commands)

except ImportError:
    setup(**params)
    raise
