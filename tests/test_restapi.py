#######################################################################
# This file is part of steve.
#
# Copyright (C) 2012-2014 Will Kahn-Greene
# Licensed under the Simplified BSD License. See LICENSE for full
# license.
#######################################################################

from steve.restapi import urljoin


def test_urljoin():
    data = [
        ('http://localhost', ['path1'], 'http://localhost/path1'),
        ('http://localhost/path1', ['path2'], 'http://localhost/path1/path2'),
        ('http://localhost', ['path1', 'path2'], 'http://localhost/path1/path2'),
        ('http://localhost?foo=bar', ['path1'], 'http://localhost/path1?foo=bar'),
    ]

    for base, args, expected in data:
        assert urljoin(base, *args) == expected
