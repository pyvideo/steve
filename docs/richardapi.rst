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

.. automodule:: steve.richardapi

   .. autofunction:: get_all_categories(api_url)

   .. autofunction:: get_category(api_url, title)

   .. autofunction:: create_category_if_missing(api_url, username, auth_key, category_data)

   .. autofunction:: create_video(api_url, username, auth_key, video_data)

   .. autofunction:: update_video(api_url, username, auth_key, video_id, video_data)

