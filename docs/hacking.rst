==================
 Hacking on steve
==================

It's likely steve will never "be done". Thus, it's likely it will be
in a perpetual need for people to tweak steve to do the things they
need it to do. These people are you!

This chapter covers contributing to steve.


Contributing
============

We use Github to host the code. After you've forked the project, make
changes like this:

1. create a branch based on master to hold your changes
2. make your changes in that branch and commit them
3. create a pull request between pyvideo/master and your branch with
   all the details you think I'll need to know to understand what you
   did, why, and what problem you were trying to solve

This is somewhat high level and sort of assumes you know git, Github,
and contributing to projects like this one. If you need more help
because these assumptions don't match you, please ask me on IRC.


Code conventions
================

PEP-8 and pyflakes is your friend.


Documenting
===========

steve documentation is in two places:

1. in the code in docstrings
2. in the ``docs/`` directory in reStructuredText files as a Sphinx
   docs project

Everything is in reStructuredText.

Generally speaking:

1. Good docs are good.
2. Bad docs are lousy.
3. Lack of docs are suboptimal.


Running and writing tests
=========================

steve comes with unit tests.  Unit tests are executed using `nose`_.
If you don't already have nose installed, then install it with::

    pip install nose

I like to use `nose-progressive`_, too, because it's awesome.  To
install that::

    pip install nose-progressive

To run the unit tests from a git clone or the source tarball, do this
from the project directory::

    nosetests

With nose-progressive and fail-fast::

    nosetests -x --with-progressive


.. _nose-progressive: http://pypi.python.org/pypi/nose-progressive/
.. _nose: http://code.google.com/p/python-nose/
