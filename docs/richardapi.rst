.. _steve-richardapi:

==========================
 Using steve - richardapi
==========================

This module holds a series of functions that use the richard API
to move data back and forth.


.. contents::
   :local:


steve.richardapi
================

.. versionadded:: 0.2

.. Note::

   Carl, Ryan: These functions are for you!

   They use an auth token. If you need an auth token, let one of the
   pyvideo admin know.

.. automodule:: steve.richardapi

   .. autofunction:: get_all_categories(api_url)

   .. autofunction:: get_category(api_url, title)

   .. autofunction:: create_video(api_url, username, auth_key, video_data)

   .. autofunction:: update_video(api_url, username, auth_key, video_id, video_data)

