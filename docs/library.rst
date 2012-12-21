.. _steve-utils:

=======================
 Using steve - library
=======================

By day, steve is a cli of world renoun. By night, steve is a Python
library capable of great cunning. This chapter covers the utility
functions.


.. contents::
   :local:


Writing steve scripts
=====================

steve can be used for batch processing a bunch of JSON files.

Most batch processing works this way:

1. get the config file (:py:func:`steve.util.get_project_config`)
2. get all the json files (:py:func:`steve.util.load_json_files`)
3. iterate through the json files transforming the data
4. save the json files (:py:func:`steve.util.save_json_files`)


steve.util
==========

.. automodule:: steve.util

   .. autofunction:: with_config(fun)

   .. autofunction:: get_project_config()

   .. autofunction:: load_json_files(config)

   .. autofunction:: save_json_files(config, data, **kw)

   .. autofunction:: save_json_file(config, filename, contents, **kw)

   .. autofunction:: scrapevideo(video_url)

   .. autofunction:: verify_json(data)

   .. autofunction:: verify_json_files(json_files)


Recipes
=======

Here's some sample code for doing batch transforms.


Update language
---------------

This fixes the `language` property in each json file. It sets it to
"Italian" if the word "Italiano" appears in the summary. Otherwise it
sets it to "English".

::

    import steve.util

    cfg = steve.util.get_project_config()
    data = steve.util.load_json_files(cfg)

    for fn, contents in data:
        print fn

        # If 'Italiana' shows up in the summary, set the language
        # to Italian.
        if 'Italiana' in contents['summary']:
            contents['language'] = u'Italian'
        else:
            contents['language'] = u'English'

    steve.util.save_json_files(cfg, data)
