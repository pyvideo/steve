#######################################################################
# This file is part of steve.
#
# Copyright (C) 2012-2014 Will Kahn-Greene
# Licensed under the Simplified BSD License. See LICENSE for full
# license.
#######################################################################

from setuptools import setup, find_packages
import re
import os


READMEFILE = 'README.rst'
VERSIONFILE = os.path.join('steve', '__init__.py')
VSRE = r"""^__version__ = ['"]([^'"]*)['"]"""


def get_version():
    verstrline = open(VERSIONFILE, 'rt').read()
    mo = re.search(VSRE, verstrline, re.M)
    if mo:
        return mo.group(1)
    else:
        raise RuntimeError(
            'Unable to find version string in {0}.'.format(VERSIONFILE))


setup(
    name='steve',
    version=get_version(),
    description='Command line importer for richard',
    long_description=open(READMEFILE).read(),
    license='Simplified BSD License',
    author='Will Kahn-Greene',
    author_email='willkg@bluesock.org',
    keywords='richard videos importer',
    url='http://github.com/pyvideo/steve',
    zip_safe=True,
    packages=find_packages(),
    include_package_data=True,
    scripts=['scripts/steve-cmd'],
    install_requires=[
        'argparse',
        'blessings',
        'cssselect',
        'html2text',
        'jinja2',
        'nose',
        ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        ],
    )
