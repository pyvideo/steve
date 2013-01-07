#######################################################################
# This file is part of steve.
#
# Copyright (C) 2012, 2013 Will Kahn-Greene
# Licensed under the Simplified BSD License. See LICENSE for full
# license.
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
    license="Simplified BSD License",
    author="Will Kahn-Greene",
    author_email="willg@bluesock.org",
    keywords="richard videos importer",
    url="http://github.com/willkg/steve",
    zip_safe=True,
    packages=find_packages(),
    scripts=['scripts/steve-cmd'],
    install_requires=[
        "argparse",
        "vidscraper",
        "blessings",
        "slumber",
        "jinja2"
        ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        ],
    )
