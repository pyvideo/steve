#######################################################################
# This file is part of steve.
#
# Copyright (C) 2012, 2013 Will Kahn-Greene
# Licensed under the Simplified BSD License. See LICENSE for full
# license.
#######################################################################

from steve import restapi
from steve.util import SteveException, verify_video_data


class MissingRequiredData(SteveException):
    """Denotes that data passed in is missing keys

    :property errors: The list of errors

    Example::

        from steve.richardapi import MissingRequiredData

        try:
            # do something here
        except MissingRequiredData as exc:
            # oh noes! i did something wrogn!

            # This prints the list of errors.
            print exc.errors

    """
    pass


class DoesNotExist(SteveException):
    """Denotes that the requested item doesn't exist"""
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


def get_category(api_url, title):
    """Gets information for specified category

    :arg api_url: URL for the api
    :arg title: title of category to retrieve

    :returns: category data

    :raises steve.richardapi.DoesNotExist: if the category doesn't
        exist

    """
    all_categories = get_all_categories(api_url)

    cats_by_title = [cat for cat in all_categories
                     if cat['title'] == title]
    if cats_by_title:
        return cats_by_title[0]

    raise DoesNotExist('category "%s" does not exist' % title)


def create_category_if_missing(api_url, username, auth_key, category_data):
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
            'carl',
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
        raise MissingRequiredData(
            'category data has errors',
            errors=['missing "title"'])

    try:
        cat = get_category(api_url, category_data['title'])
        return cat

    except DoesNotExist:
        pass

    api = restapi.API(api_url)
    return restapi.get_content(api.category.post(category_data,
                                                 username=username,
                                                 api_key=auth_key))


def create_video(api_url, username, auth_key, video_data):
    """Creates a video on the site

    This creates a video on the site using HTTP POST. It returns
    the video data it posted which also contains the id.

    .. Note::

       This doesn't yet check to see if the video already exists.

    :arg api_url: URL for the api
    :arg username: username
    :arg auth_key: auth key for that username for that API URL
    :arg video_data: Python dict holding the values to create
        this video

    :returns: the video data

    :raises steve.restapi.Http5xxException: if there's a server
        error
    :raises steve.richardapi.MissingRequiredData: if the video_data
        is missing keys that are required---check the ``errors``
        property of the exception for a list of errors

    Example::

        import datetime

        from steve.util import create_video, MissingRequiredData

        try:
            video = create_video(
                'http://pyvideo.org/api/v1/',
                'carl',
                'ou812authkey',
                {
                    'category': 'Test Category',
                    'state': 1,
                    'title': 'Test video title',
                    'speakers': ['Jimmy Discotheque'],
                    'language': 'English',
                    'added': datetime.datetime.now().isoformat()
                })
       
            # Prints the video data.
            print video

        except MissingRequiredData as exc:
            # Prints the errors
            print exc.errors


    .. Note::

       Check the richard project in the video app at ``models.py`` for
       up-to-date list of fields and their types.

       https://github.com/willkg/richard/blob/master/richard/videos/models.py

    """
    errors = verify_video_data(video_data)

    if errors:
        raise MissingRequiredData(
            'video data has errors', errors=errors)

    # TODO: Check to see if the video exists already. Probably
    # want to use (category, title) as a key.

    api = restapi.API(api_url)
    return restapi.get_content(api.video.post(video_data,
                                              username=username,
                                              api_key=auth_key))

