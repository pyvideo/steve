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
3. iterate through the json files transforming the data (Python for loop)
4. save the json files (:py:func:`steve.util.save_json_files`)


steve.util
==========

.. automodule:: steve.util

   .. autofunction:: with_config(fun)

   .. autofunction:: get_project_config()

   .. autofunction:: html_to_markdown(text)

   .. autofunction:: load_json_files(config)

   .. autofunction:: save_json_files(config, data, **kw)

   .. autofunction:: save_json_file(config, filename, contents, **kw)

   .. autofunction:: scrape_videos(url)

   .. autofunction:: scrape_video(video_url)

   .. autofunction:: verify_video_data(data)

   .. autofunction:: verify_json_files(json_files)

   .. autofunction:: get_video_id(richard_url)


Recipes
=======

Here's some sample code for doing batch transforms. Each script should
be located in the project directory root next to the ``steve.ini`` file.
Make sure the steve package is installed and then run the script with
the python interpreter::

    python name_of_my_script.py

Or however you want to structure and/or run it.


Update language
---------------

This fixes the `language` property in each json file. It sets it to
"Italian" if the word "Italiana" appears in the summary. Otherwise it
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


Move speaker from summary to speakers
-------------------------------------

This removes the first line of the summary and puts it in the speakers
field.

::

    import steve.util

    cfg = steve.util.get_project_config()
    data = steve.util.load_json_files(cfg)

    for fn, contents in data:
        print fn

        # If the data already has speakers, then we assume we've already
        # operated on it and don't operate on it again.
        if contents['speakers']:
            continue

        summary = contents['summary']
        summary = summary.split('\n')

        # The speakers field is a list of strings. So we remove the first
        # line of the summary, strip the whitespace from it, and put that
        # in the speakers field.
        # (NB: This bombs out if the summary field is empty.)
        contents['speakers'].append(summary.pop(0).strip())

        # Put the rest of the summary back.
        contents['summary'] = '\n'.join(summary)

    steve.util.save_json_files(cfg, data)


Convert summary and description to Markdown
-------------------------------------------

This converts summary and description to Markdown.

::

    import steve.util

    cfg = steve.util.get_project_config()
    data = steve.util.load_json_files(cfg)

    for fn, contents in data:
        print fn

        contents['summary'] = steve.util.html_to_markdown(
            contents.get('summary', ''))

        contents['description'] = steve.util.html_to_markdown(
            contents.get('description', ''))

    steve.util.save_json_files(cfg, data)
