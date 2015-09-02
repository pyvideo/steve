#######################################################################
# This file is part of steve.
#
# Copyright (C) 2012-2014 Will Kahn-Greene
# Licensed under the Simplified BSD License. See LICENSE for full
# license.
#######################################################################

import ConfigParser
import datetime
import json
import os
import string
import sys
import textwrap
import unicodedata
from functools import wraps
from urlparse import urlparse

import html2text


def is_youtube(url):
    parsed = urlparse(url)
    return parsed.netloc.startswith(
        ('www.youtube.com', 'youtube.com', 'youtu.be'))


ALLOWED_LETTERS = string.ascii_letters + string.digits + '-_'


class SteveException(Exception):
    """Base steve exception"""
    def __init__(self, *args, **kwargs):
        self.__dict__.update(kwargs)
        super(SteveException, self).__init__(*args)


class ConfigNotFound(SteveException):
    """Denotes the config file couldn't be found"""
    pass


class Config(object):
    def __init__(self):
        self._file_name = None

    def initialise(self):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def get(self, section, key):
        raise NotImplementedError


class IniConfig(Config):
    file_name = 'steve.ini'

    def __init__(self):
        super(IniConfig, self).__init__()

    def load(self):
        """Finds and opens the config file in the current directory

        :raises ConfigNotFound: if the config file can't be found

        :returns: config file

        """
        # TODO: Should we support parent directories, too?
        projectpath = os.getcwd()
        path = os.path.join(projectpath, 'steve.ini')
        if not os.path.exists(path):
            projectpath = os.path.dirname(projectpath)
            path = os.path.join(projectpath, 'steve.ini')
            if not os.path.exists(path):
                raise ConfigNotFound('steve.ini could not be found.')

        self._data = cp = ConfigParser.ConfigParser()
        cp.read(path)

        # TODO: This is a little dirty since we're inserting stuff into
        # the config file if it's not there, but so it goes.
        try:
            cp.get('project', 'projectpath')
        except ConfigParser.NoOptionError:
            cp.set('project', 'projectpath', projectpath)
        try:
            cp.get('project', 'jsonpath')
        except ConfigParser.NoOptionError:
            cp.set('project', 'jsonpath', os.path.join(cp.get('project', 'projectpath'), 'json'))
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

        return self

    def get(self, section, key):
        return self._data.get(section, key)

    _CONFIG = textwrap.dedent("""\
    [project]
    # The name of this group of videos. For example, if this was a conference
    # called EuroPython 2011, then you'd put:
    # category = EuroPython 2011
    category =

    # The url for where all the videos are listed.
    # e.g. url = http://www.youtube.com/user/PythonItalia/videos
    url =

    # The projectpath is where steve assumes subdirs if not explitly set
    # projectpath = {projectpath}
    # The jsonpath, if set, is where steve will look for the JSON files
    # jsonpath = {jsonpath}

    # The url for the richard instance api.
    # e.g. url = http://example.com/api/v1/
    api_url =

    # Your username and api key.
    #
    # Alternatively, you can pass this on the command line or put it in a
    # separate API_KEY file which you can keep out of version control.
    # e.g. username = willkg
    #      api_key = OU812
    # username =
    # api_key =
    """)

    def create(self, dir_path):
        abs_path = os.path.abspath(dir_path)
        kw = dict(
            projectpath=abs_path,
            jsonpath=os.path.join(abs_path, 'json')
        )
        with open(os.path.join(dir_path, self.file_name), 'w') as fp:
            fp.write(self._CONFIG.format(**kw))


SteveConfig = IniConfig   # to allow easy switching in the future


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
    ...     print 'Config!: {0!r}'.format(cfg)
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
      or parent directory

    :raises ConfigNotFound: if the config file can't be found

    :returns: config file

    """
    return SteveConfig().load()


def get_project_config_file_name():
    """
    :returns: config file basename
    """
    return SteveConfig.file_name


def create_project_config_file(dir_path):
    """Creates a new config file in directory

    :param dir_path: directory in which to create the config file

    :returns: config file basename
    """
    SteveConfig().create(dir_path)


def get_from_config(cfg, key, section='project',
                    error='"{key}" must be defined in steve.ini file.'):
    """Retrieves specified key from config or errors

    :arg cfg: the configuration
    :arg key: key to retrieve
    :arg section: the section to retrieve the key from
    :arg error: the error to print to stderr if the key is not
        there or if the value is empty. ``{key}`` gets filled in
        with the key

    """
    try:
        value = cfg.get(section, key)
        if value:
            return value.strip()
    except ConfigParser.NoOptionError:
        pass

    err(error.format(key=key))
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
            return obj.strftime('%Y-%m-%d')
        return obj

    return json.dumps(structure, indent=2, sort_keys=True, default=convert)


def generate_filename(text):
    filename = text.replace(' ', '_')
    filename = ''.join([c for c in filename if c in ALLOWED_LETTERS])
    return filename


def get_video_requirements():
    fn = os.path.join(os.path.dirname(__file__), 'video_reqs.json')
    fp = open(fn)
    data = json.load(fp)
    fp.close()
    return data


def _required(data):
    if (data['null'] or data['has_default'] or data['empty_strings']):
        return False
    return True


def verify_video_data(data, category=None):
    """Verify the data in a single json file for a video.

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

            if not category and key not in data:
                errors.append(
                    '"category" must be in either steve.ini or data file')
            elif (key in data and (
                    category is not None and data[key] != category)):
                errors.append(
                    '"{0}" field does not match steve.ini category'.format(
                        key))

        elif key not in data:
            # Required data must be there.

            # TODO: We add title here because this is the client side
            # of the API and that's a special case that's differen
            # than the data model which is where the video_reqs.json
            # are derived. That should get fixed in richard.
            if _required(req) or key == 'title':
                errors.append('"{0}" field is required'.format(key))

        elif req['type'] == 'IntegerField':
            if not isinstance(data[key], int):
                if ((_required(req)
                     or (not _required(req) and data[key] is not None))):

                    errors.append('"{0}" field must be an int'.format(key))
            elif req['choices'] and data[key] not in req['choices']:
                errors.append(
                    '"{0}" field must be one of {1}'.format(
                        key, req['choices']))

        elif req['type'] == 'TextField':
            if not req['empty_strings'] and not data[key]:
                errors.append(
                    '"{0}" field can\'t be an empty string'.format(key))
            elif not data[key]:
                continue

        elif req['type'] == 'TextArrayField':
            for mem in data[key]:
                if not mem:
                    errors.append(
                        '"{0}" field has empty strings in it'.format(key))
                    break

        elif req['type'] == 'BooleanField':
            if data[key] not in (True, False):
                errors.append('"{0}" field has non-boolean value'.format(key))

    required_keys = [req['name'] for req in requirements]

    # Second check to make sure there aren't fields that shouldn't
    # be there.
    for key in data.keys():
        # Ignore special cases. These will be there if the data
        # was pulled via the richard API or if we did a push.
        if key in ['id', 'updated']:
            continue

        if key not in required_keys:
            errors.append('"{0}" field shouldn\'t be there.'.format(key))

    return errors


def verify_json_files(json_files, category=None):
    """Verifies the data in a bunch of json files.

    Prints the output

    :param json_files: list of (filename, parsed json data) tuples to
        call :py:func:`verify_video_data` on

    :param category: The category as specified in the steve.ini file.

        If the steve.ini has a category, then every data file either
        has to have the same category or no category at all.

        This is None if no category is specified in which case every
        data file has to have a category.

    :returns: dict mapping filenames to list of error strings
    """
    filename_to_errors = {}

    for filename, data in json_files:
        filename_to_errors[filename] = verify_video_data(data, category)

    return filename_to_errors


def wrap(text, indent=''):
    return (
        textwrap.TextWrapper(initial_indent=indent, subsequent_indent=indent)
        .wrap(text))


def err(*output, **kw):
    """Writes output to stderr.

    :arg wrap: If you set ``wrap=False``, then ``err`` won't textwrap
        the output.

    """
    output = 'Error: ' + ' '.join([str(o) for o in output])
    if kw.get('wrap') is not False:
        output = '\n'.join(wrap(output, kw.get('indent', '')))
    elif kw.get('indent'):
        indent = kw['indent']
        output = indent + ('\n' + indent).join(output.splitlines())
    sys.stderr.write(output + '\n')


def stringify(blob):
    if isinstance(blob, unicode):
        return unicodedata.normalize('NFKD', blob).encode('ascii', 'ignore')
    return str(blob)


def out(*output, **kw):
    """Writes output to stdout.

    :arg wrap: If you set ``wrap=False``, then ``out`` won't textwrap
        the output.

    """
    output = ' '.join([stringify(o) for o in output])
    if kw.get('wrap') is not False:
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
    jsonpath = config.get('project', 'jsonpath')

    if not os.path.exists(jsonpath):
        return []

    files = [f for f in os.listdir(jsonpath) if f.endswith('.json')]

    data = []

    for fn in sorted(files):
        try:
            full_path = full_path = os.path.join(jsonpath, fn)
            fp = open(full_path, 'r')
            data.append((fn, json.load(fp)))
            fp.close()
        except Exception, e:
            err('Problem with {0}'.format(full_path), wrap=False)
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

    jsonpath = config.get('project', 'jsonpath')
    if not os.path.exists(jsonpath):
        os.makedirs(jsonpath)

    for fn, contents in data:
        assert os.sep not in fn
        full_path = os.path.join(jsonpath, fn)
        fp = open(full_path, 'w')
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

    jsonpath = config.get('project', 'jsonpath')
    if not os.path.exists(jsonpath):
        os.makedirs(jsonpath)

    assert os.sep not in filename
    full_path = os.path.join(jsonpath, filename)

    fp = open(full_path, 'w')
    json.dump(contents, fp, **kw)
    fp.close()


def scrape_videos(url):
    """Scrapes a url for video data. Returns list of dicts.

    :arg url: The url to fetch data from

    :returns: list of dicts

    >>> scrape_videos('https://www.youtube.com/user/PyConDE/videos')
    [...]

    """
    # FIXME: generate list of available scrapers.
    # FIXME: run url through all available scrapers.
    from steve.scrapers import YoutubeScraper
    return YoutubeScraper().scrape(url)


def scrape_video(url):
    """Scrapes the url and fixes the data

    :arg url: Url of video to scrape.

    :returns: Python dict of metadata

    Example:

    >>> scrape_video('http://www.youtube.com/watch?v=ywToByBkOTc')
    {'url': 'http://www.youtube.com/watch?v=ywToByBkOTc', ...}

    """
    # FIXME: generate list of available scrapers.
    # FIXME: run url through all available scrapers.
    from steve.scrapers import YoutubeScraper
    data = YoutubeScraper().scrape(url)
    return data


def html_to_markdown(text):
    """Converts an HTML string to equivalent Markdown

    :arg text: the HTML string to convert

    :returns: Markdown string

    Example:

    >>> html_to_markdown('<p>this is <b>html</b>!</p>')
    u'this is **html**!'

    """
    return html2text.html2text(text).strip()


def get_video_id(richard_url):
    """Given a richard url for a video, returns the video id as an int

    :arg richard_url: url for a video on a richard instance

    :returns: video id as an integer

    :throws SteveException: if it has problems parsing the video id
        out of the url

    Example:

    >>> get_video_id("http://pyvideo.org/video/2822/make-api-calls")
    2822
    >>> get_video_id('foo')
    Traceback (most recent call last):
      File ...
    SteveException: could not parse out video id

    """
    try:
        return int(richard_url.split('/video/')[1].split('/')[0])
    except (AttributeError, IndexError, ValueError):
        raise SteveException('Could not parse video id')
