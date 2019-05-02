# setup file for only the framework part of Omnivore_framework. Includes:
#
# Enthought (traits, traitsui, pyface, apptools, envisage)
# pyfilesystem
#
import os
import sys
from setuptools import find_packages
from setuptools import setup


full_version = "4.0"

packages = find_packages()
print(packages)

setup(
    name = 'omnivore-framework',
    version = full_version,
    author = "Rob McMullen",
    author_email = "feedback@playermissile.com",
    url = "http://playermissile.com",
    download_url = "https://pypi.org/project/omnivore-framework/",
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
    description = "Dependency target for mapping applications",
    long_description = open('README.rst').read(),
    ext_modules = [],
    install_requires = ["numpy"],
    setup_requires = ["numpy"],
    license = "GPL",
    packages = packages,
    package_data = {},
    data_files={},
    entry_points = {},
    options={},
    platforms = ["Windows", "Linux", "Mac OS-X", "Unix"],
    zip_safe = False,
    )
