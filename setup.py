# setup file for only the framework part of Omnivore_framework. Includes:
#
# Enthought (traits, traitsui, pyface, apptools, envisage)
# pyfilesystem
#
import os
import sys
import shutil
import glob
import subprocess
from setuptools import find_packages
from setuptools import setup
from distutils.extension import Extension

install_requires = [
    'numpy',
    'jsonpickle>=0.9.4',
    'bson<1.0.0',
    'configobj',
    'pyparsing',
    'pytz',
    'traits>=4.6',
    'wxpython>=4.0.3'
    ]


cmdclass = dict()

import omnivore_framework
full_version = omnivore_framework.__version__
spaceless_version = full_version.replace(" ", "_")

common_includes = [
    "ctypes",
    "ctypes.util",
    "wx.lib.pubsub.*",
    "wx.lib.pubsub.core.*",
    "wx.lib.pubsub.core.kwargs.*",
    "multiprocessing",
    "pkg_resources",
    "configobj",
    
    "traits",
]
common_includes.extend(omnivore_framework.get_py2exe_toolkit_includes())

py2app_includes = [
]

common_excludes = [
    "test",
#    "unittest", # needed for numpy
    "pydoc_data",
     "Tkconstants",
    "Tkinter", 
    "tcl", 
    "_imagingtk",
    "PIL._imagingtk",
    "ImageTk",
    "PIL.ImageTk",
    "FixTk",
    ]

py2exe_excludes = [
    ]

# package_data is for pip and python installs, not for app bundles. Need
# to use data_files for that
package_data = {
    'omnivore_framework': ['icons/*.png',
                 'icons/*.ico',
                 'templates/*',
                 ],
    }

# Must explicitly add namespace packages
packages = find_packages()
packages.append("omnivore_framework.editors")


base_dist_dir = "dist-%s" % spaceless_version
win_dist_dir = os.path.join(base_dist_dir, "win")
mac_dist_dir = os.path.join(base_dist_dir, "mac")

is_64bit = sys.maxsize > 2**32

options = {}

# data files are only needed when building an app bundle
data_files = []

setup(
    name = 'omnivore-framework',
    version = full_version,
    author = omnivore_framework.__author__,
    author_email = omnivore_framework.__author_email__,
    url = omnivore_framework.__url__,
    download_url = ('%s/%s.tar.gz' % (omnivore_framework.__download_url__, full_version)),
    classifiers = [c.strip() for c in """\
        Development Status :: 5 - Production/Stable
        Intended Audience :: Developers
        License :: OSI Approved :: GNU General Public License (GPL)
        Operating System :: MacOS
        Operating System :: Microsoft :: Windows
        Operating System :: OS Independent
        Operating System :: POSIX
        Operating System :: Unix
        Programming Language :: Python
        Topic :: Utilities
        Topic :: Software Development :: Assemblers
        Topic :: Software Development :: Disassemblers
        """.splitlines() if len(c.strip()) > 0],
    description = "Simple wxPython UI application framework",
    long_description = open('README.rst').read(),
    cmdclass = cmdclass,
    ext_modules = [],
    install_requires = install_requires,
    setup_requires = ["numpy"],
    license = "GPL",
    packages = packages,
    package_data = package_data,
    data_files=data_files,
    entry_points={
        "omnivore_framework.loaders": [
            'fleep = omnivore_framework.loaders.fleep',
            'text = omnivore_framework.loaders.text',
        ],
    },
    options=options,
    platforms = ["Windows", "Linux", "Mac OS-X", "Unix"],
    zip_safe = False,
    )
