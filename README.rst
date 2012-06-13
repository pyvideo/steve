=======
 steve 
=======

Summary
=======

`richard <https://github.com/willkg/richard>`_ is a video index
site. It has a very basic admin interface for adding videos by hand
one-by-one. This gets very tedious when adding all the videos for a
conference.

`steve <https://github.com/willkg/steve>`_ is a command line utility
for downloading information for a conference, downloading all the
metadata for the videos, and making it easier to transform the data,
fix it and make it better.

richard and steve go together like peanut butter and jelly. You could
use one without the other, but it's daft. steve uses richard's API for
pulling/pushing video data.

It solves this use case:

    MAL sends Will a request to add the EuroPython 2011 videos to 
    pyvideo.org. The EuroPython 2011 videos are on YouTube. Will uses
    steve to download all the data for the conference on YouTube, then
    uses steve to apply some transforms on the data, then uses steve
    to edit each video individually and finally uses steve to push
    all the data (the new conference, new videos, speakers, tags) to
    pyvideo.org.


Features
========

May 29th, 2012: I just started working on steve---it has no features,
yet.


History
=======

I've been working on richard since March 2012. I knew I needed steve
and had some thoughts on how it should work, but there were a bunch of
things I wanted to do with richard, so I pushed work on steve off.

Then on May 29th, 2012, I finished up the initial bits of steve and
thus steve was born.


License, etc
============

steve Copyright(C) 2012 Will Kahn-Greene

This program comes with ABSOLUTELY NO WARRANTY.  This is free software,
and you are welcome to redistribute it under certain conditions.  See
the Terms and Conditions section of `LICENSE`_ for details.

.. _LICENSE: http://www.gnu.org/licenses/gpl-3.0.html


Install
=======

Released version
----------------

If you want a released version of steve, do this:

1. ``pip install steve``


Bleeding edge version
---------------------

If you want a bleeding edge version of steve, do this:

1. ``git clone git://github.com/willkg/steve.git``
2. ``cd steve``
3. ``python setup.py install`` or ``python setup.py develop``


Bleeding edge for hacking purposes
----------------------------------

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


Run
===

For list of subcommands, arguments and other help, do this::

    steve-cmd --help


Example use
===========

.. Note::

   This is a conceptual example! None of this is implemented, yet!

1. Install steve.

2. Run: ``steve-cmd createproject europython2011``

   This creates a ``europython2011`` directory for project files.

   In that directory is:

   1. a ``steve.ini`` project config file.
   2. a ``json`` directory which hold the video metadata json files.

3. ``cd europython2011``

4. Edit ``steve.ini``::

       [project]
       # The name of this group of videos. For example, if this was a conference
       # called EuroPython 2011, then you'd put:
       # category = EuroPython 2011
       category = EuroPython 2011

       # The url for where all the videos are listed.
       # e.g. url = http://www.youtube.com/user/PythonItalia/videos
       url = http://www.youtube.com/user/PythonItalia/videos

       # If the url is a YouTube-based url, you can either have 'object'
       # based embed code or 'iframe' based embed code. Specify that
       # here.
       youtube_embed = object

5. Run: ``steve-cmd fetch``

   This fetches the video metadata from that YouTube user and
   generates a series of JSON files---one for each video---and puts
   them in the ``json`` directory.

   The format for each file matches the format expected by the richard
   API.

6. Run: ``steve-cmd status``

   Lists filenames for all videos that have a non-empty whiteboard
   field. Because you've just downloaded the metadata, all of the
   videos have a whiteboard field stating they haven't been edited,
   yet.

   .. Note::

      If you pass in ``--list``, it'll print out a list of the files
      one per line making it easier to use with other command line
      utilities.

7. Run: ``steve-cmd ls``

   Lists titles and some other data for each video in the set.

8. Edit the metadata. When you're done with a video, make sure to
   clear the whiteboard field.

   TODO: steve should make this easier

9. Run: ``steve-cmd push http://example.com/api/v1/``

   This pushes the new videos to your richard instance.

That's it!

.. Note::

   I highly recommend you use version control for your steve project
   and back up the data to a different machine periodically. It
   doesn't matter which version control system you use. It doesn't
   matter how you back it up. However, it does matter that you do
   these things so you aren't sad later on when the inevitable
   happens.


Test
====

steve comes with unit tests.  Unit tests are executed using `nose`_ and
use `fudge`_ as a mocking framework.  If you don't already have nose
and fudge installed, then install them with::

    pip install nose fudge

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
.. _fudge: http://farmdev.com/projects/fudge/


Source code
===========

Source code is hosted on github.

https://github.com/willkg/steve


Issue tracker
=============

Issue tracker is hosted on github.

https://github.com/willkg/steve/issues


Resources I found helpful
=========================

* `vidscraper <https://github.com/pculture/vidscraper>`_ and the
  `vidscraper documentation
  <http://vidscraper.readthedocs.org/en/latest/>`_
