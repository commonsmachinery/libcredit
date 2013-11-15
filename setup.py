#! /usr/bin/env python

from distutils.core import setup
from DistUtilsExtra.command import (build_extra, build_i18n)

setup(
    name='libcredit.py',
    version='0.1.0',

    url = 'https://github.com/commonsmachinery/libcredit',
    author = 'Commons Machinery http://commonsmachinery.se/',
    author_email = '<dev@commonsmachinery.se>',
    description = 'Generate attribution and license messages from RDF metadata',
    license = 'GPLv2',

    py_modules=['libcredit'],
    package_dir = { '': 'python' },
    cmdclass={
        "build": build_extra.build_extra,
        "build_i18n": build_i18n.build_i18n,
    },

    classifiers = [
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ]
)
