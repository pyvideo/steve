#######################################################################
# This file is part of steve.
#
# Copyright (C) 2012, 2013 Will Kahn-Greene
# Licensed under the Simplified BSD License. See LICENSE for full
# license.
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

    :raises ConfigNotFound: if the config file can't be found

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

    # If STEVE_CRED_FILE is specified in the environment or there's a
    # cred_file in the config file, then open the file and pull the
    # API information from there:
    #
    # * api_url
    # * username
    # * api_key
    #
    # This allows people to have a whole bunch of steve project
    # directories and store their credentials in a central location.
    cred_file = None
    try:
        cred_file = os.environ['STEVE_CRED_FILE']
    except KeyError:
        try:
            cred_file = cp.get('project', 'cred_file')
        except ConfigParser.NoOptionError:
            pass

    if cred_file:

        cred_file = os.path.abspath(cred_file)

        if os.path.exists(cred_file):
            cfp = ConfigParser.ConfigParser()
            cfp.read(cred_file)
            cp.set('project', 'api_url', cfp.get('default', 'api_url'))
            cp.set('project', 'username', cfp.get('default', 'username'))
            cp.set('project', 'api_key', cfp.get('default', 'api_key'))

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

    if video.files:
        for f in video.files:
            if f.mime_type in ('video/ogg', 'video/ogv'):
                item['video_ogv_length'] = f.length
                item['video_ogv_url'] = f.url
                item['video_ogv_download_only'] = False
            elif f.mime_type == 'video/mp4':
                item['video_mp4_length'] = f.length
                item['video_mp4_url'] = f.url
                item['video_mp4_download_only'] = False
            elif f.mime_type == 'video/webm':
                item['video_webm_length'] = f.length
                item['video_webm_url'] = f.url
                item['video_webm_download_only'] = False
            elif f.mime_type == 'video/x-flv':
                item['video_flv_length'] = f.length
                item['video_flv_url'] = f.url
                item['video_flv_download_only'] = False
            else:
                raise ValueError('No clue what to do with %s' % f.mime_type)

    item['embed'] = video.embed_code

    if (youtube_embed is not None and 'youtube.com' in video.link
        and hasattr(video, 'guid')):

        guid = video.guid
        if guid:
            guid = video.guid.split('/')[-1]
            item['embed'] = youtube_embed % {'guid': guid}

    return item


def get_video_requirements():
    fn = os.path.join(os.path.dirname(__file__), 'video_reqs.json')
    fp = open(fn)
    data = json.load(fp)
    fp.close()
    return data


def _required(data):
    if (data['null']
        or data['has_default']
        or data['empty_strings']):
        return False
    return True


def verify_json(data, category=None):
    """Verify the data in a single json file.

    :param data: The parsed contents of a JSON file. This should be a
        Python dict.
    :param category: The category as specified in the steve.ini file.

        If the steve.ini has a category, then every data file either
        has to have the same category or no category at all.

        This is None if no category is specified in which case every
        data file has to have a category.

    :returns: list of error strings.
    """

    # TODO: rewrite this to return a dict of fieldname -> list of
    # errors
    errors = []
    requirements = get_video_requirements()

    # First, verify the data is correct.
    for req in requirements:
        key = req['name']

        if key == 'category':
            # Category is a special case since we can specify it
            # in the steve.ini file.

            if category is None and key not in data:
                errors.append(
                    '"category" must be in either steve.ini or data file')
            elif key in data and data[key] != category:
                errors.append(
                    '"%s" field does not match steve.ini category' % key)

        elif _required(req) and key not in data:
            errors.append('"%s" field is required' % key)

        elif req['null'] and data.get(key) == None:
            continue

        elif req['type'] == 'IntegerField':
            if not isinstance(data[key], int):
                errors.append('"%s" field must be an int' % key)
            elif req['choices'] and data[key] not in req['choices']:
                errors.append('"%s" field must be one of %s' % (
                        key, req.choices))

        elif req['type'] == 'TextField':
            if not req['empty_strings'] and not data[key]:
                errors.append('"%s" field can\'t be an empty string' % key)
            elif not data[key]:
                continue
            elif req['html'] and not '<' in data[key]:
                errors.append('"%s" field should be HTML formatted' % key)

        elif req['type'] == 'TextArrayField':
            for mem in data[key]:
                if not mem:
                    errors.append('"%s" field has empty strings in it' % key)
                    break

    required_keys = [req['name'] for req in requirements]

    # Second check to make sure there aren't fields that shouldn't
    # be there.
    for key in data.keys():
        # Ignore special cases. These will be there if the data
        # was pulled via the richard API or if we did a push.
        if key in ['id', 'updated']:
            continue

        if key not in required_keys:
            errors.append('"%s" field shouldn\'t be there.' % key)

    return errors


def verify_json_files(json_files, category=None):
    """Verifies the data in a bunch of json files.

    Prints the output

    :param json_files: list of (filename, parsed json data) tuples to
        call verify_json on

    :param category: The category as specified in the steve.ini file.

        If the steve.ini has a category, then every data file either
        has to have the same category or no category at all.

        This is None if no category is specified in which case every
        data file has to have a category.

    :returns: dict mapping filenames to list of error strings
    """
    filename_to_errors = {}

    for filename, data in json_files:
        filename_to_errors[filename] = verify_json(data, category)

    return filename_to_errors


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

    projectpath = config.get('project', 'projectpath')
    jsonpath = os.path.join(projectpath, 'json')
    if not os.path.exists(jsonpath):
        os.makedirs(jsonpath)

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
