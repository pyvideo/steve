#######################################################################
# This file is part of steve.
#
# Copyright (C) 2012 Will Kahn-Greene
#
# steve is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# steve is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with steve.  If not, see <http://www.gnu.org/licenses/>.
#######################################################################


import argparse
import ConfigParser
import datetime
import json
import os
import sys
import textwrap
from functools import wraps

import vidscraper

YOUTUBE_EMBED = {
    'object': ('<object width="640" height="390"><param name="movie" '
               'value="http://youtube.com/v/%(guid)s?version=3&amp;hl=en_US"></param>'
               '<param name="allowFullScreen" value="true"></param>'
               '<param name="allowscriptaccess" value="always"></param>'
               '<embed src="http://youtube.com/v/%(guid)s?version=3&amp;hl=en_US" '
               'type="application/x-shockwave-flash" width="640" '
               'height="390" allowscriptaccess="always" '
               'allowfullscreen="true"></embed></object>'),
    'iframe': ('<iframe id="player" width="640" height="390" frameborder="0" '
               'src="http://youtube.com/v/%(guid)s"></iframe>')
    }


class BetterArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        if 'byline' in kwargs:
            self.byline = kwargs.pop('byline')
        else:
            self.byline = None
        argparse.ArgumentParser.__init__(self, *args, **kwargs)

    def print_byline(self, file=None):
        if file is None:
            file = sys.stdout
        if self.byline:
            self._print_message(self.byline + '\n', file)

    def print_usage(self, file=None):
        self.print_byline(file)
        argparse.ArgumentParser.print_usage(self, file)


class ConfigNotFound(Exception):
    pass


def with_config(fun):
    @wraps(fun)
    def _with_config(*args, **kwargs):
        try:
            cfg = get_project_config()
        except ConfigNotFound:
            err('Could not find steve.ini project config file.')
            return 1
        return fun(cfg, *args, **kwargs)
    return _with_config


def get_project_config():
    # TODO: Should we support parent directories, too?
    projectpath = os.getcwd()
    path = os.path.join(projectpath, 'steve.ini')
    if not os.path.exists(path):
        raise ConfigNotFound()

    cp = ConfigParser.ConfigParser()
    cp.read(path)

    # TODO: This is a little dirty since we're inserting stuff into
    # the config file if it's not there, but so it goes.
    try:
        cp.get('project', 'projectpath')
    except ConfigParser.NoOptionError:
        cp.set('project', 'projectpath', projectpath)

    return cp


def convert_to_json(structure):
    def convert(obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.strftime('%Y-%m-%dT%H:%M:%SZ')
        return obj

    return json.dumps(structure, indent=2, sort_keys=True, default=convert)


def wrap(text, indent=''):
    return (
        textwrap.TextWrapper(initial_indent=indent, subsequent_indent=indent)
        .wrap(text))


def wrap_paragraphs(text):
    text = ['\n'.join(textwrap.wrap(mem)) for mem in text.split('\n\n')]
    return '\n\n'.join(text)


def err(*output, **kwargs):
    """Writes output to stderr.

    :arg wrap: If you set ``wrap=False``, then ``err`` won't textwrap
        the output.

    """
    output = 'Error: ' + ' '.join([str(o) for o in output])
    if kwargs.get('wrap') != False:
        output = '\n'.join(wrap(output, kwargs.get('indent', '')))
    elif kwargs.get('indent'):
        indent = kwargs['indent']
        output = indent + ('\n' + indent).join(output.splitlines())
    sys.stderr.write(output + '\n')


def stringify(blob):
    if isinstance(blob, unicode):
        return blob.encode('ascii', 'ignore')
    return str(blob)


def out(*output, **kwargs):
    """Writes output to stdout.

    :arg wrap: If you set ``wrap=False``, then ``out`` won't textwrap
        the output.

    """
    output = ' '.join([stringify(o) for o in output])
    if kwargs.get('wrap') != False:
        output = '\n'.join(wrap(output, kwargs.get('indent', '')))
    elif kwargs.get('indent'):
        indent = kwargs['indent']
        output = indent + ('\n' + indent).join(output.splitlines())
    sys.stdout.write(output + '\n')


def load_json_files(config):
    """Parses and returns all video files for a project

    :returns: list of (filename, data) tuples
    """
    projectpath = config.get('project', 'projectpath')
    jsonpath = os.path.join(projectpath, 'json')

    if not os.path.exists(jsonpath):
        return []

    files = [f for f in os.listdir(jsonpath) if f.endswith('.json')]
    files = [os.path.join('json', f) for f in files]
    files.sort()

    data = []

    for fn in files:
        try:
            fp = open(fn, 'r')
            data.append((fn, json.load(fp)))
            fp.close()
        except Exception, e:
            err('Problem with %s' % fn, wrap=False)
            raise e

    return data


def save_json_files(config, data, **kwargs):
    """Saves json files

    :arg config: configuration object
    :arg data: list of (filename, data) tuples
    """
    if 'indent' not in kwargs:
        kwargs['indent'] = 2

    if 'sort_keys' not in kwargs:
        kwargs['sort_keys'] = True

    for fn, contents in data:
        fp = open(fn, 'w')
        json.dump(contents, fp, **kwargs)
        fp.close()


def save_json_file(config, fn, contents, **kwargs):
    """Saves a single json file

    :arg config: configuration object
    :arg fn: filename
    :arg contents: python dict to save
    """
    if 'indent' not in kwargs:
        kwargs['indent'] = 2

    if 'sort_keys' not in kwargs:
        kwargs['sort_keys'] = True

    fp = open(fn, 'w')
    json.dump(contents, fp, **kwargs)
    fp.close()


def video_to_json(url, video, **kwargs):
    data = dict([(field, getattr(video, field))
                 for field in video.fields])

    for field in ('publish_datetime', 'file_url_expires'):
        dt = data.get(field, None)
        if isinstance(dt, datetime.datetime):
            data[field] = dt.isoformat()

    data['url'] = url
    if 'youtube.com' in url:
        guid = data['guid'].split('/')[-1]
        data['object_embed_code'] = (YOUTUBE_EMBED['object'] %
                                     {'guid': guid})
        data['iframe_embed_code'] = (YOUTUBE_EMBED['iframe'] %
                                     {'guid': guid})

    return json.dumps(data, **kwargs)


def scrapevideo(video_url):
    video_data = vidscraper.auto_scrape(video_url)
    return video_to_json(video_url, video_data, indent=2, sort_keys=True)
