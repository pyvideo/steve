#######################################################################
# This file is part of steve.
#
# Copyright (C) 2012, 2013 Will Kahn-Greene
# Licensed under the Simplified BSD License. See LICENSE for full
# license.
#######################################################################

from steve import restapi
from steve.util import SteveException


class MissingRequiredData(SteveException):
    """Denotes that data passed in is missing keys"""
    pass


def get_all_categories(api_url):
    """Given an api_url, retrieves all categories

    :arg api_url: URL for the api.

    :returns: list of dicts each belonging to a category

    :raises steve.restapi.Http5xxException: if there's a server
        error

    Example::

        from steve.util import get_all_categories

        cats = get_all_categories('http://pyvideo.org/api/v1/')
        print [cat['title'] for cat in cats]

        # Prints something like:
        # [u'PyCon 2012', u'PyCon 2011', etc.]

    """
    api = restapi.API(api_url)

    # Build a dict of cat title -> cat data.
    all_categories = restapi.get_content(api.category.get(limit=0))

    return all_categories['objects']


def create_category_if_not_exists(api_url, username, auth_key,
                                  category_data):
    """Creates a category on the site if it doesn't already exist

    This checks to see if the category is already on the site by
    checking titles and slugs.

    If the category does not exist, it creates it and returns the new
    category data.

    If the category does exist, then it just returns the category.

    :arg api_url: URL for the api
    :arg username: username
    :arg auth_key: auth key for that username for that API URL
    :arg category_data: Python dict holding the values to create
        this category

    :returns: the category data

    :raises steve.restapi.Http5xxException: if there's a server
        error
    :raises steve.richardapi.MissingRequiredData: if the category_data
        is missing keys that are required

    Example::

        from steve.util import create_category_if_not_exists

        cat = create_category_if_not_exists(
            'http://pyvideo.org/api/v1/',
            'carlfk',
            'ou812authkey',
            {'title': 'Test Category 2013'})
       
        print cat
        # Prints something like:
        # {u'description': u'', u'videos': [],
        #  u'title': u'Test Category 2013', u'url': u'',
        #  u'whiteboard': u'', u'start_date': None,
        #  u'id': u'114', u'slug': u'test-category-2013',
        #  u'resource_uri': u'/api/v1/category/114/'}


    .. Note::

       Check the richard project in the video app at ``models.py`` for
       up-to-date list of fields and their types.

       https://github.com/willkg/richard/blob/master/richard/videos/models.py

    """

    if not 'title' in category_data or not category_data['title']:
        raise MissingRequiredData('category "title" missing.')

    all_categories = get_all_categories(api_url)

    cats_by_title = [cat for cat in all_categories
                     if cat['title'] == category_data['title']]
    if cats_by_title:
        return cats_by_title[0]

    api = restapi.API(api_url)
    return restapi.get_content(api.category.post(category_data,
                                                 username=username,
                                                 api_key=auth_key))
