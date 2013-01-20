.. _steve-restapi:

=======================
 Using steve - restapi
=======================

"steve comes with its own REST client API."

"Seriously? There are dozens out there? Why roll your own?"

"Because the one I was using had issues and wasn't being updated. I
decided it was easier to just roll my own for my limited needs. Plus
it was kind of fun to write."

"Dude. steve is turning into a Frankenstein monster monstrosity. You
need to see the doctor to cure you of your NIH syndrome."

"Shh... I'm busy."


.. contents::
   :local:


Using the REST client API by itself
===================================

It's similar to slumber except a little less feature(bug)-full.
The gist of it is this:

1. Import some stuff::

       from steve.restapi import API, RestAPIException, get_content

2. Build an `API` object::

       api = API('http://localhost/v1/api/')

3. Use the `API` object to fiddle with resources::

       # Get all videos
       all_videos = api.video.get()

       # Get video with id 1
       video_1 = get_content(api.video(1).get())

       # Change the data, then put it
       video_1['somekey'] = 'newvalue'
       api.video(1).put(data=video_1)

       # Create a new video. This does a POST and if there's
       # a 201, it'll return the results of that.
       newvideo = get_content(api.video.post(data={'somekey': 'newvalue'}))

That's pretty much it!

Why `get_content`? That way you're guaranteed that you have the
requests `Response` object so you can see what's going on. That makes
this REST client API a bit easier to debug---it's just a thin layer on
top of `requests <http://docs.python-requests.org/en/latest/>`_.


steve.restapi
=============

.. automodule:: steve.restapi

   .. autofunction:: get_content(resp)

   .. autoclass:: API

   .. autoclass:: Resource

   .. autoclass:: RestAPIException

   .. autoclass:: Http4xxException

   .. autoclass:: Http5xxException
