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
            print exc

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

    # Build a dict of cat title -> cat data
    resp = restapi.get_content(api.category.get(limit=0))

    return resp['results']


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

    raise DoesNotExist('category "{0}" does not exist'.format(title))


def create_video(api_url, auth_token, video_data):
    """Creates a video on the site

    This creates a video on the site using HTTP POST. It returns
    the video data it posted which also contains the id.

    .. Note::

       This doesn't yet check to see if the video already exists.

    :arg api_url: URL for the api
    :arg auth_token: auth token
    :arg video_data: Python dict holding the values to create
        this video

    :returns: the video data

    :raises steve.restapi.Http5xxException: if there's a server
        error
    :raises steve.richardapi.MissingRequiredData: if the video_data
        is missing keys that are required

    Example::

        import datetime

        from steve.util import create_video, MissingRequiredData

        try:
            video = create_video(
                'http://pyvideo.org/api/v1/',
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
            print exc


    .. Note::

       Check the richard project in the video app at ``models.py`` for
       up-to-date list of fields and their types.

       https://github.com/willkg/richard/blob/master/richard/videos/models.py

    """
    errors = verify_video_data(video_data)

    if errors:
        raise MissingRequiredData(
            'video data has errors: {0}'.format(repr(errors)))

    # TODO: Check to see if the video exists already. Probably
    # want to use (category, title) as a key.

    api = restapi.API(api_url)
    return restapi.get_content(
        api.video.post(data=video_data, auth_token=auth_token))


def update_video(api_url, auth_token, video_id, video_data):
    """Updates an existing video on the site

    This updates an existing video on the site using HTTP PUT. It
    returns the final video data.

    .. Warning::

       This stomps on the data that's currently there. If you have the
       video_id wrong, then this will overwrite the current data.

       Be very careful about updating existing video data. Best to get
       it, make sure the id is correct (check the title? the slug?),
       and then update it.


    :arg api_url: URL for the api
    :arg auth_token: auth token
    :arg video_id: The id for the video
    :arg video_data: Python dict holding all the data for this video

    :returns: the updated video data

    :raises steve.restapi.Http4xxException: if the video doesn't
        exist on the server
    :raises steve.restapi.Http5xxException: if there's a server
        error
    :raises steve.richardapi.MissingRequiredData: if the video_data
        is missing keys that are required


    Example::

        import datetime

        from steve.util import update_video, MissingRequiredData

        try:
            video = update_video(
                'http://pyvideo.org/api/v1/',
                'ou812authkey',
                1101,
                {
                    'id': 1101,
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
            print exc


    .. Note::

       Check the richard project in the video app at ``models.py`` for
       up-to-date list of fields and their types.

       https://github.com/willkg/richard/blob/master/richard/videos/models.py

    """
    # If you do a create_video, then update that data and do an
    # update_video, the data has a few fields in it that shouldn't be
    # there. We nix those here.
    video_data.pop('resource_uri', None)
    video_data.pop('added', None)

    errors = verify_video_data(video_data)

    if errors:
        raise MissingRequiredData(
            'video data has errors: {0}'.format(repr(errors)))

    api = restapi.API(api_url)

    # Try to get the video on the site. This will kick up a 404
    # if it doesn't exist.
    api.video(video_id).get(auth_token=auth_token)

    # Everything is probably fine, so try to update the data.
    return restapi.get_content(
        api.video(video_id).put(data=video_data,
                                auth_token=auth_token))
