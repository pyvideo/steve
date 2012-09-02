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
    'object': (
        '<object width="640" height="390"><param name="movie" '
        'value="http://youtube.com/v/%(guid)s?version=3&amp;hl=en_US"></param>'
        '<param name="allowFullScreen" value="true"></param>'
        '<param name="allowscriptaccess" value="always"></param>'
        '<embed src="http://youtube.com/v/%(guid)s?version=3&amp;hl=en_US" '
        'type="application/x-shockwave-flash" width="640" '
        'height="390" allowscriptaccess="always" '
        'allowfullscreen="true"></embed></object>'),
    'iframe': (
        '<iframe id="player" width="640" height="390" frameborder="0" '
        'src="http://youtube.com/v/%(guid)s"></iframe>')
    }


class BetterArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kw):
        if 'byline' in kw:
            self.byline = kw.pop('byline')
        else:
            self.byline = None
        argparse.ArgumentParser.__init__(self, *args, **kw)

    def print_byline(self, file=None):
        if file is None:
            file = sys.stdout
        if self.byline:
            self._print_message(self.byline + '\n', file)

    def print_usage(self, file=None):
        self.print_byline(file)
        argparse.ArgumentParser.print_usage(self, file)


class ConfigNotFound(Exception):
    """Denotes the config file couldn't be found"""


def with_config(fun):
    """Decorator that passes config as first argument

    This calls :py:func:`get_project_config`. If that returns a
    configuration object, then this passes that as the first argument
    to the decorated function. If :py:func:`get_project_config` doesn't
    return a config object, then this raises :py:exc:`ConfigNotFound`.

    Example:

    >>> @with_config
    ... def config_printer(cfg):
    ...     print 'Config!: %r' % cfg
    ...
    >>> config_printer()  # if it found a config
    Config! ...
    >>> config_printer()  # if it didn't find a config
    Traceback
        ...
    steve.util.ConfigNotFound: steve.ini could not be found.
    """
    @wraps(fun)
    def _with_config(*args, **kw):
        cfg = get_project_config()
        return fun(cfg, *args, **kw)
    return _with_config


def get_project_config():
    """Finds and opens the config file in the current directory

    :raises ConfigNotFound: if the config file can't be found

    :returns: config file

    """
    # TODO: Should we support parent directories, too?
    projectpath = os.getcwd()
    path = os.path.join(projectpath, 'steve.ini')
    if not os.path.exists(path):
        raise ConfigNotFound('steve.ini could not be found.')

    cp = ConfigParser.ConfigParser()
    cp.read(path)

    # TODO: This is a little dirty since we're inserting stuff into
    # the config file if it's not there, but so it goes.
    try:
        cp.get('project', 'projectpath')
    except ConfigParser.NoOptionError:
        cp.set('project', 'projectpath', projectpath)

    # API_KEY file overrides api_key set in config file.
    apikey_path = os.path.join(projectpath, 'API_KEY')
    if os.path.exists(apikey_path):
        api_key = open(apikey_path).read().strip()
        cp.set('project', 'api_key', api_key)

    return cp


def get_from_config(cfg, key, section='project',
                    error='"%(key)s" must be defined in steve.ini file.'):
    """Retrieves specified key from config or errors

    :arg cfg: the configuration
    :arg key: key to retrieve
    :arg section: the section to retrieve the key from
    :arg error: the error to print to stderr if the key is not
        there or if the value is empty

    """
    try:
        value = cfg.get(section, key)
        if value:
            return value.strip()
    except ConfigParser.NoOptionError:
        pass

    err(error % {'key': key})
    return None


def load_tags_file(config):
    """Opens the tags file and loads tags

    The tags file is either specified in the ``tagsfile`` config
    entry or it's ``PROJECTPATH/tags.txt``.

    The file consists of a list of tags---one per line. Blank lines
    and lines that start with ``#`` are removed.

    This will read the file and return the list of tags.

    If the file doesn't exist, this returns an empty list.

    :arg config: the project config file

    :returns: list of strings

    """
    projectpath = config.get('project', 'projectpath')
    try:
        tagsfile = config.get('project', 'tagsfile')
    except ConfigParser.NoOptionError:
        tagsfile = 'tags.txt'

    tagsfile = os.path.join(projectpath, tagsfile)
    if not os.path.exists(tagsfile):
        return []

    fp = open(tagsfile, 'r')
    tags = [tag.strip() for tag in fp.readlines()]
    fp.close()

    # Nix blank lines and lines that start with #.
    return [tag for tag in tags if tag and not tag.startswith('#')]


def convert_to_json(structure):
    def convert(obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.strftime('%Y-%m-%dT%H:%M:%SZ')
        return obj

    return json.dumps(structure, indent=2, sort_keys=True, default=convert)


def vidscraper_to_dict(video, youtube_embed=None):
    """Converts vidscraper Video to a python dict

    :arg video: vidscraper Video
    :arg youtube_embed: the embed code to use for YouTube videos

    :returns: dict

    """
    item = {}

    item['state'] = 2  # STATE_DRAFT
    item['whiteboard'] = u'needs editing'

    item['title'] = video.title
    item['category'] = 0
    item['summary'] = video.description
    item['description'] = u''
    item['quality_notes'] = u''
    item['slug'] = u''
    item['source_url'] = video.link
    item['copyright_text'] = video.license

    item['tags'] = video.tags
    item['speakers'] = []

    item['added'] = datetime.datetime.now()
    item['recorded'] = video.publish_datetime
    item['language'] = u'English'

    item['thumbnail_url'] = video.thumbnail_url

    if video.file_url_mimetype:
        if video.file_url_mimetype in ('video/ogg', 'video/ogv'):
            item['video_ogv_length'] = video.file_url_length
            item['video_ogv_url'] = video.file_url
            item['video_ogv_download_only'] = False
        elif video.file_url_mimetype == 'video/mp4':
            item['video_mp4_length'] = video.file_url_length
            item['video_mp4_url'] = video.file_url
            item['video_mp4_download_only'] = False
        elif video.file_url_mimetype == 'video/webm':
            item['video_webm_length'] = video.file_url_length
            item['video_webm_url'] = video.file_url
            item['video_webm_download_only'] = False
        elif video.file_url_mimetype == 'video/x-flv':
            item['video_flv_length'] = video.file_url_length
            item['video_flv_url'] = video.file_url
            item['video_flv_download_only'] = False
        else:
            raise ValueError('No clue what to do with %s' %
                         video.file_url_mimetype)

    item['embed'] = video.embed_code

    if (youtube_embed is not None and 'youtube.com' in video.link
        and hasattr(video, 'guid')):

        guid = video.guid
        if guid:
            guid = video.guid.split('/')[-1]
            item['embed'] = youtube_embed % {'guid': guid}

    return item


def wrap(text, indent=''):
    return (
        textwrap.TextWrapper(initial_indent=indent, subsequent_indent=indent)
        .wrap(text))


def wrap_paragraphs(text):
    text = ['\n'.join(textwrap.wrap(mem)) for mem in text.split('\n\n')]
    return '\n\n'.join(text)


def err(*output, **kw):
    """Writes output to stderr.

    :arg wrap: If you set ``wrap=False``, then ``err`` won't textwrap
        the output.

    """
    output = 'Error: ' + ' '.join([str(o) for o in output])
    if kw.get('wrap') != False:
        output = '\n'.join(wrap(output, kw.get('indent', '')))
    elif kw.get('indent'):
        indent = kw['indent']
        output = indent + ('\n' + indent).join(output.splitlines())
    sys.stderr.write(output + '\n')


def stringify(blob):
    if isinstance(blob, unicode):
        return blob.encode('ascii', 'ignore')
    return str(blob)


def out(*output, **kw):
    """Writes output to stdout.

    :arg wrap: If you set ``wrap=False``, then ``out`` won't textwrap
        the output.

    """
    output = ' '.join([stringify(o) for o in output])
    if kw.get('wrap') != False:
        output = '\n'.join(wrap(output, kw.get('indent', '')))
    elif kw.get('indent'):
        indent = kw['indent']
        output = indent + ('\n' + indent).join(output.splitlines())
    sys.stdout.write(output + '\n')


def load_json_files(config):
    """Parses and returns all video files for a project

    :arg config: the configuration object
    :returns: list of (filename, data) tuples where filename is the
        string for the json file and data is a Python dict of
        metadata.

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


def save_json_files(config, data, **kw):
    """Saves a bunch of files to json format

    :arg config: the configuration object
    :arg data: list of (filename, data) tuples where filename is the
        string for the json file and data is a Python dict of metadata

    .. Note::

       This is the `save` side of :py:func:`load_json_files`. The output
       of that function is the `data` argument for this one.

    """
    if 'indent' not in kw:
        kw['indent'] = 2

    if 'sort_keys' not in kw:
        kw['sort_keys'] = True

    for fn, contents in data:
        fp = open(fn, 'w')
        json.dump(contents, fp, **kw)
        fp.close()


def save_json_file(config, filename, contents, **kw):
    """Saves a single json file

    :arg config: configuration object
    :arg filename: filename
    :arg contents: python dict to save
    :arg kw: any keyword arguments accepted by `json.dump`

    """
    if 'indent' not in kw:
        kw['indent'] = 2

    if 'sort_keys' not in kw:
        kw['sort_keys'] = True

    fp = open(filename, 'w')
    json.dump(contents, fp, **kw)
    fp.close()


def scrapevideo(video_url):
    """Scrapes the url and fixes the data

    This is sort of a wrapper around `vidscraper.auto_scrape`. It
    calls that, but then transforms the results into a Python dict and
    adds some additional computed metadata.

    :arg video_url: Url of video to scrape.

    :returns: Python dict of metadata

    Example:

    >>> scrapevideo('http://www.youtube.com/watch?v=ywToByBkOTc')
    {'url': 'http://www.youtube.com/watch?v=ywToByBkOTc', ...}

    """
    video_data = vidscraper.auto_scrape(video_url)

    data = dict([(field, getattr(video_data, field))
                 for field in video_data.fields])

    for field in ('publish_datetime', 'file_url_expires'):
        dt = data.get(field, None)
        if isinstance(dt, datetime.datetime):
            data[field] = dt.isoformat()

    data['url'] = video_url
    if 'youtube.com' in video_url and 'guid' in data and data['guid']:
        guid = data['guid'].split('/')[-1]
        data['object_embed_code'] = (YOUTUBE_EMBED['object'] %
                                     {'guid': guid})
        data['iframe_embed_code'] = (YOUTUBE_EMBED['iframe'] %
                                     {'guid': guid})

    return data
