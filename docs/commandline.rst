===========================
 Using steve - commandline
===========================

For list of subcommands, arguments and other help, do this::

    steve-cmd --help


Example use
===========

.. Note::

   This is a conceptual example! Only some of this is vaguely
   implemented!

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

   One way to do this is to do::

       steve-cmd status --list | xargs vim

   and edit them by hand one-by-one.

   TODO: steve should make this easier---provide batch transforms?

9. Run: ``steve-cmd check``

   This goes through all the json files and verifies correctness. Are
   all the required key/value pairs present? Are the values of the
   correct type? Are values that should be in HTML in HTML? Is the
   HTML well-formed? Etc.

10. Run: ``steve-cmd push http://example.com/api/v1/``

    This pushes the new videos to your richard instance.

That's it!

.. Note::

   I highly recommend you use version control for your steve project
   and back up the data to a different machine periodically. It
   doesn't matter which version control system you use. It doesn't
   matter how you back it up. However, it does matter that you do
   these things so you aren't sad later on when the inevitable
   happens.


