=============
 About steve
=============

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
    to edit each video individually and finally uses steve to push all
    the data (the new conference, new videos, speakers, tags) to
    pyvideo.org.


History
=======

I've been working on richard since March 2012. I knew I needed steve
and had some thoughts on how it should work, but there were a bunch of
things I wanted to do with richard, so I pushed work on steve off.

Then on May 29th, 2012, I finished up the initial bits of steve and
thus steve was born.

I worked on it on and off while simultaneously working on adding the
EuroPython 2011 conference videos to `pyvideo.org
<http://pyvideo.org/>`_ and helping Carl with some of the conferences
he was working on.
