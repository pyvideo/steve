===========================
 Using steve - commandline
===========================

For list of subcommands, arguments and other help, do this::

    steve-cmd --help


Example use
===========

.. Note::

   This is a quick tutorial---you don't have to use steve like
   this. Use it in a way that makes your work easier!

1. Install steve.

2. Run: ``steve-cmd createproject europython2011``

   This creates a ``europython2011`` directory for project files.

   In that directory is:

   1. a ``steve.ini`` project config file.
   2. a ``json`` directory which hold the video metadata json files.

3. ``cd europython2011``

4. Edit ``steve.ini``::

       [project] 

       # The name of this group of videos. For example, if this was a
       # conference called EuroPython 2011, then you'd put:
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

8. Edit the json metadata. When you're done with a video, make sure to
   clear the whiteboard field.

   You can use the ``status`` command to make this easier::

       steve-cmd status --list | xargs vim

   and edit them by hand one-by-one.

   You can also write a script which uses functions in ``steve.util``
   to automate fixing the metadata.

   For example, here's a script that takes the summary data, converts it
   from reStructuredText to HTML and puts it in the description field::

       from docutils.core import publish_parts

       from steve.util import (get_project_config, load_json_files,
           save_json_files)


       cfg = get_project_config()
       data = load_json_files(cfg)


       def parse(text):
           settings = {
               'initial_header_level': 2,
               'transform_doctitle': 1
               }
           parts = publish_parts(
               text, writer_name='html', settings_overrides=settings)
           return parts['body']


       for fn, contents in data:
           print fn

           summary = contents['summary'].strip()
           summary_parsed = parse(summary)
           if 'ERROR' in summary_parsed or 'WARNING' in summary_parsed:
               print 'problem with %s' % fn
               raise ValueError()

           if not contents['description']:
               contents['description'] = parse(summary)


       save_json_files(cfg, data)


   Conference data varies pretty widely, so writing scripts to
   batch-process it to handle issues like this is super
   helpful. Automate anything you can.

   See the API documentation in :ref:`steve-utils`.

9. Run: ``steve-cmd verify``

   This goes through all the json files and verifies correctness.

   Is the data of the correct type and shape?

   Are required fields present?

   Are values that should be in HTML in HTML?

10. If you have write access for the API of the server, then you can
    do::

        steve-cmd push

    Otherwise, tar up the project directory and send it to someone
    who does.


That's it!

.. Note::

   I highly recommend you use version control for your steve project
   and back up the data to a different machine periodically. It
   doesn't matter which version control system you use. It doesn't
   matter how you back it up. However, it does matter that you do
   these things so you aren't sad later on when the inevitable
   happens.


