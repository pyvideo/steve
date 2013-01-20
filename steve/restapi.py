#######################################################################
# This file is part of steve.
#
# Copyright (C) 2012, 2013 Will Kahn-Greene
# Licensed under the Simplified BSD License. See LICENSE for full
# license.
#######################################################################

"""
This is a REST client API since steve does a bunch of REST things
with richard's API. It's a slim layer on top of requests.
"""

import json
import urlparse

import requests


class RestAPIException(Exception):
    def __init__(self, *args, **kwargs):
        self.__dict__.update(kwargs)
        super(RestAPIException, self).__init__(*args)


class Http4xxException(RestAPIException):
    """Exception for 4xx errors.

    These usually mean you did something wrong.

    :property response: The full requests `Response` object.

    Example::

        from steve.restapi import Http4xxException

        try:
            # do something here
        except Http5xxException as exc:
            # oh noes! i did something wrogn!

            # This tells you the actual HTTP status code
            print exc.response.status_code

            # This tells you the content of the response---sometimes
            # the server will tell you an error message and it's
            # probably in here.
            print exc.response.content

    """
    pass


class Http5xxException(RestAPIException):
    """Exception for 5xx errors.

    These usually mean the server did something wrong. Let me know.

    :property response: The full requests `Response` object.

    Example::

        from steve.restapi import Http5xxException

        try:
            # do something here
        except Http5xxException as exc:
            # oh noes! i hit dumb willkg code and server is br0ken!

            # This tells you the actual HTTP status code
            print exc.response.status_code

            # This tells you the content of the response---sometimes
            # the server will tell you an error message and it's
            # probably in here.
            print exc.response.content

    """

    pass


def urljoin(base, *args):
    """Add bits to the url path."""
    parts = list(urlparse.urlsplit(base))
    path = [p for p in parts[2].split('/') if p]
    path.extend(args)
    parts[2] = '/'.join(path)
    return urlparse.urlunsplit(parts)


def get_content(resp):
    """Returns the JSON content from a response.

    .. Note::

       Mostly this just deals with the fact that requests changed
       `.json` from a property to a method. Once that settles out and
       we can use requests >= 1.0, then we can ditch this.
    """
    try:
        # requests changed from a .json property to a .json method,
        # so, deal with both here.
        if callable(resp.json):
            return resp.json()
        else:
            return resp.json

    except Exception as exc:
        # TODO: Fix this. The requests docs say that .json throws an
        # exception but doesn't specify which one. Need to toss some
        # bad "json" at it and see what it does so we can make this
        # except suck less.
        print 'Error: get_content threw %s' % exc
        return resp.text


class Resource(object):
    """Convenience wrapper for requests.request.

    HTTP methods return requests Response objects or throw
    exceptions in cases where things are weird.
    """
    def __init__(self, **kwargs):
        self._kwargs = kwargs
        url = kwargs['url']
        if not url.endswith('/'):
            url = url + '/'

        id_ = kwargs.get('id')
        if id_:
            url = urljoin(url, id_)

        self._kwargs['url'] = url
        self.session = requests.session()

    def __call__(self, id_):
        kwargs = dict(self._kwargs)
        kwargs['id'] = id_
        return Resource(**kwargs)

    def _request(self, method, data=None, params=None, headers=None,
                 url=None):
        if not url:
            url = self._kwargs['url']

        default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'}
        if headers:
            default_headers.update(headers)

        resp = self.session.request(method, url, data=data, params=params,
                                    headers=default_headers)

        if 400 <= resp.status_code <= 499:
            raise Http4xxException(
                'HTTP %s: %s %s' % (resp.status_code, method, url),
                response=resp)
        elif 500 <= resp.status_code <= 599:
            raise Http5xxException(
                'HTTP %s: %s %s' % (resp.status_code, method, url),
                response=resp)

        return resp

    def get(self, **kwargs):
        resp = self._request('GET', params=kwargs)
        if 200 <= resp.status_code <= 299:
            return resp
        raise RestAPIException('Unknown response: %s' % resp.status_code,
                               response=resp)

    def post(self, data, **kwargs):
        jsondata = json.dumps(data)

        resp = self._request('POST', data=jsondata, params=kwargs)

        if resp.status_code in (201, 301, 302, 303, 307):
            location = resp.headers['location']
            return self._request('GET', params=kwargs, url=location)

        elif 200 <= resp.status_code <= 299:
            return resp

        raise RestAPIException('Unknown response: %s' % resp.status_code,
                               response=resp)

    def put(self, data, **kwargs):
        jsondata = json.dumps(data)

        resp = self._request('PUT', data=jsondata, params=kwargs)

        if resp.status_code in (201, 301, 302, 303, 307):
            location = resp.headers['location']
            return self._request('GET', params=kwargs, url=location)

        elif 200 <= resp.status_code <= 299:
            return resp

        raise RestAPIException('Unknown response: %s' % resp.status_code,
                               response=resp)

    def delete(self, **kwargs):
        resp = self._request('DELETE', params=kwargs)
        if 200 <= resp.status_code <= 299:
            return resp
        raise RestAPIException('Unknown response: %s' % resp.status_code,
                               response=resp)


class API(object):
    """Convenience wrapper around requests.

    Example::

        from steve.restapi import API

        # Creates an api endpoint
        api = API('http://pyvideo.org/v1/api/')

        # Does a get for all videos
        all_videos = api.video.get()

        # Does a get for video with a specific id
        video_1 = api.video(1).get()

        # Update the data and then put it
        video_1['somekey'] = 'newvalue'
        api.video(1).put(data=video_1)

        # Create a new video. This does a POST and if there's a
        # redirect, will pick that up.
        newvideo = api.video.post(data={'somekey': 'newvalue'})
    """

    def __init__(self, base_url):
        self.base_url = base_url

    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]

        return Resource(url=urljoin(self.base_url, key))
