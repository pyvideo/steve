.. _installation:

==============
 Installation
==============

There are a few ways to install steve. This document covers them.

.. contents::
   :local:


Installing a released version
=============================

You can install steve using pip::

    pip install steve


Installing a bleeding edge version
==================================

If you want a bleeding edge version of steve, you can either
install with pip from a git url or clone the project and install
that.

pip and git urls:

    Install like this:

    1. ``pip install git+https://github.com/willkg/steve.git``

    Update like this:

    1. ``pip install -U git+https://github.com/willkg/steve.git``


git clone and installing from that:

    Install like this:

    1. ``git clone git://github.com/willkg/steve.git``
    2. ``cd steve``
    3. ``python setup.py develop``

    Update like this:

    1. ``cd steve``
    2. ``git checkout master``
    3. ``git pull --rebase``


Installing a Bleeding edge for hacking purposes
===============================================

If you want to install steve in a way that makes it easy to hack on,
do this:

1. ``git clone git://github.com/willkg/steve.git``
2. ``cd steve``
3. ``virtualenv ./venv/``
4. ``./venv/bin/python setup.py develop``

When you want to use steve from your virtual environment, make sure to
activate the virtual environment first. e.g.:

1. ``. ./venv/bin/activate``
2. ``steve-cmd --help``
