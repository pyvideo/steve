#######################################################################
# This file is part of steve.
#
# Copyright (C) 2012 Will Kahn-Greene
# 
# steve is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# steve is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with steve.  If not, see <http://www.gnu.org/licenses/>.
#######################################################################

from setuptools import setup, find_packages
import re
import os


READMEFILE = "README.rst"
VERSIONFILE = os.path.join("steve", "_version.py")
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"


def get_version():
    verstrline = open(VERSIONFILE, "rt").read()
    mo = re.search(VSRE, verstrline, re.M)
    if mo:
        return mo.group(1)
    else:
        raise RuntimeError(
            "Unable to find version string in %s." % VERSIONFILE)


setup(
    name="steve",
    version=get_version(),
    description="Command line importer for richard",
    long_description=open(READMEFILE).read(),
    license="GPL",
    author="Will Kahn-Greene",
    author_email="willg@bluesock.org",
    keywords="richard videos importer",
    url="http://github.com/willkg/steve",
    zip_safe=True,
    packages=find_packages(),
    scripts=['scripts/steve-cmd'],
    install_requires=[
        "argparse",
        "vidscraper==0.5.2",
        "blessings",
        "slumber",
        ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        ],
    )
