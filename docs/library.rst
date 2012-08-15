=======================
 Using steve - library
=======================

By day, steve is a cli of world renoun. By night, steve is a Python
library capable of great cunning. This chapter covers the utility
functions.


steve.util
==========

.. automodule:: steve.util

   .. autofunction:: get_project_config()

   .. autofunction:: load_json_files(config)

   .. autofunction:: save_json_files(config, data, **kw)

   .. autofunction:: save_json_file(config, filename, contents, **kw)

   .. autofunction:: scrapevideo(video_url)


Recipes
=======

Here's some sample code for doing batch transforms.


Update language
===============

This fixes the `language` property in each json file. It sets it to
"Italian" if the word "Italiano" appears in the summary. Otherwise it
sets it to "English".

::

    import steve

    cfg = steve.get_project_config()
    data = steve.load_json_files(cfg)

    for fn, contents in data:
        print fn

        if 'Italiana' in contents['summary']:
            contents['language'] = u'Italian'
        else:
            contents['language'] = u'English'

    steve.save_json_files(cfg, data)


Most batch processing works this way:

1. get the config file
2. get all the json files
3. iterate through the json files doing some transform
4. save the json files
