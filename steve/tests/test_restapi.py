from unittest import TestCase

from nose.tools import eq_

from steve.restapi import urljoin


class UrlJoinTestCase(TestCase):
    def test_urljoin(self):
        for base, args, expected in [
            ('http://localhost', ['path1'],
             'http://localhost/path1'),

            ('http://localhost/path1', ['path2'],
             'http://localhost/path1/path2'),

            ('http://localhost', ['path1', 'path2'],
             'http://localhost/path1/path2'),

            ('http://localhost?foo=bar', ['path1'],
             'http://localhost/path1?foo=bar'),
            ]:

            eq_(urljoin(base, *args), expected)
