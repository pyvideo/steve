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

import ConfigParser
import argparse
import blessings
import datetime
import os
import string
import sys

import slumber
import vidscraper

try:
    import steve
except ImportError:
    sys.stderr.write(
        'The steve library is not on your sys.path.  Please install steve.\n')
    sys.exit(1)

from steve.util import YOUTUBE_EMBED


BYLINE = ('steve-cmd: %s (%s).  Licensed under the GPLv3.' % (
        steve.__version__, steve.__releasedate__))

USAGE = 'Usage: steve [program-options] COMMAND [command-options] ARGS'

DESC = """
Command line interface for steve.
"""

CONFIG = """[project]
# The name of this group of videos. For example, if this was a conference
# called EuroPython 2011, then you'd put:
# category = EuroPython 2011
category =

# The url for where all the videos are listed.
# e.g. url = http://www.youtube.com/user/PythonItalia/videos
url =

# If the url is a YouTube-based url, you can either have 'object'
# based embed code or 'iframe' based embed code. Specify that
# here.
# youtube_embed = object

# The url for the richard instance api.
# e.g. url = http://example.com/api/v1/
api_url =

# Your api key.
#
# Alternatively, you can pass this on the command line or put it in a
# separate API_KEY file which you can keep out of version control.
# e.g. api_key = OU812
# api_key =
"""

ALLOWED_LETTERS = string.ascii_letters + string.digits + '-_'


def monkeypatch_slumber():
    def post(self, data, **kwargs):
        s = self.get_serializer()

        resp = self._request("POST", data=s.dumps(data), params=kwargs)
        if 200 <= resp.status_code <= 299:
            if resp.status_code == 201:
                # @@@ Hacky, see description in __call__
                resource_obj = self(url_override=resp.headers["location"])
                return resource_obj.get(**kwargs)
            else:
                return resp.content
        else:
            # @@@ Need to be Some sort of Error Here or Something
            return

    slumber.Resource.post = post


monkeypatch_slumber()


def createproject_cmd(parser, parsed):
    if not parsed.quiet:
        parser.print_byline()

    path = os.path.abspath(parsed.directory)
    if os.path.exists(path):
        steve.err('%s exists. Remove it and try again or try again with '
                  'a different filename.' % path)
        return 1

    # TODO: this kicks up errors. catch the errors and tell the user
    # something more useful
    steve.out('Creating directory %s...' % path)
    os.makedirs(path)

    steve.out('Creating steve.ini...')
    f = open(os.path.join(path, 'steve.ini'), 'w')
    f.write(CONFIG)
    f.close()

    steve.out('%s created.' % path)
    steve.out('')

    steve.out('Now cd into the directory and edit the steve.ini file.')
    steve.out('After you do that, you should put your project into version '
              'control. Srsly.')
    return 0


def vidscraper_to_richard(video, youtube_embed=None):
    """Converts a vidscraper video to a richard item

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
        elif video.file_url_mimetype == 'video/mp4':
            item['video_mp4_length'] = video.file_url_length
            item['video_mp4_url'] = video.file_url
        elif video.file_url_mimetype == 'video/webm':
            item['video_webm_length'] = video.file_url_length
            item['video_webm_url'] = video.file_url
        elif video.file_url_mimetype == 'video/x-flv':
            item['video_flv_length'] = video.file_url_length
            item['video_flv_url'] = video.file_url
        else:
            raise ValueError('No clue what to do with %s' %
                         video.file_url_mimetype)

    if 'youtube' in video.link:
        item['embed'] = youtube_embed % {'youtubeurl': video.link}
    else:
        item['embed'] = video.embed_code

    return item


@steve.with_config
def fetch_cmd(cfg, parser, parsed):
    if not parsed.quiet:
        parser.print_byline()

    projectpath = cfg.get('project', 'projectpath')
    jsonpath = os.path.join(projectpath, 'json')

    if not os.path.exists(jsonpath):
        os.makedirs(jsonpath)

    try:
        url = cfg.get('project', 'url')
    except ConfigParser.NoOptionError:
        steve.err('url not specified in steve.ini project config file.')
        steve.err('Add "url = ..." to [project] section of steve.ini file.')
        return 1

    if 'youtube' in url:
        try:
            youtube_embed = YOUTUBE_EMBED[cfg.get('project', 'youtube_embed')]
        except KeyError:
            steve.err('youtube_embed must be either "iframe" or "object".')
            return 1
    else:
        youtube_embed = None

    steve.out('Scraping %s...' % url)
    video_feed = vidscraper.auto_feed(url, crawl=True)
    video_feed.load()

    print 'Found %d videos...' % video_feed.entry_count
    for i, video in enumerate(video_feed):
        if video.title:
            filename = video.title.replace(' ', '_')
            filename = ''.join([c for c in filename if c in ALLOWED_LETTERS])
            filename = '_' + filename
        else:
            filename = ''

        filename = '%04d%s.json' % (i, filename[:40])

        print 'Working on %s... (%s)' % (video.title, filename)
        item = vidscraper_to_richard(video, youtube_embed=youtube_embed)

        f = open(os.path.join('json', filename), 'w')
        f.write(steve.convert_to_json(item))
        f.close()

        # TODO: what if there's a file there already? on the first one,
        # prompt the user whether to stomp on existing files or skip.
    return 0


@steve.with_config
def status_cmd(cfg, parser, parsed):
    if not parsed.quiet and not parsed.list:
        parser.print_byline()

    if not parsed.list and not parsed.quiet:
        steve.out('Video status:')

    files = steve.load_json_files(cfg)

    if not files:
        if not parsed.list:
            steve.out('No files')
        return 0

    term = blessings.Terminal()

    done_files = []
    in_progress_files = []

    for fn, contents in files:
        whiteboard = contents.get('whiteboard')
        if whiteboard:
            in_progress_files.append(fn)
        else:
            done_files.append(fn)

    if parsed.list:
        for fn in in_progress_files:
            steve.out(fn, wrap=False)

    else:
        if in_progress_files:
            for fn in in_progress_files:
                steve.out(u'%s: %s' % (fn, term.bold(whiteboard)),
                          wrap=False)

        if done_files:
            steve.out('')
            for fn in done_files:
                steve.out('%s: %s' % (fn, term.bold(term.green('Done!'))),
                          wrap=False)

        steve.out('')
        steve.out('In progress: %3d' % len(in_progress_files))
        steve.out('Done:        %3d' % len(done_files))

    return 0


def scrapevideo_cmd(parser, parsed):
    if not parsed.quiet:
        parser.print_byline()

    video_url = parsed.video[0]
    print steve.scrapevideo(video_url)

    return 0


@steve.with_config
def push_cmd(cfg, parser, parsed):
    if not parsed.quiet:
        parser.print_byline()

    # Get username, api_url and api_key.

    try:
        username = cfg.get('project', 'username')
        if not username:
            steve.err('"username" must be defined in steve.ini file.')
            return 1
    except ConfigParser.NoOptionError:
        steve.err('"username" must be defined in steve.ini file.')
        return 1

    try:
        api_url = cfg.get('project', 'api_url')
        if not api_url:
            steve.err('"api_url" must be defined in steve.ini file.')
            return 1
    except ConfigParser.NoOptionError:
        steve.err('"api_url" must be defined in steve.ini file.')
        return 1

    api_key = parsed.apikey
    if not api_key:
        projectpath = cfg.get('project', 'projectpath')
        apikey_path = os.path.join(projectpath, 'API_KEY')
        if os.path.exists(apikey_path):
            api_key = open(apikey_path).read().strip()
    if not api_key:
        try:
            api_key = cfg.get('project', 'api_key')
        except ConfigParser.NoOptionError:
            pass
    if not api_key:
        steve.err('Specify an api key either in steve.ini, on command line, '
                  'or in API_KEY file.')
        return 1

    username = username.strip()
    api_url = api_url.strip()
    api_key = api_key.strip()

    data = steve.load_json_files(cfg)

    # There are two modes:
    #
    # 1. User set category in configuration. Then the json files can
    #    either have no category set or they have to have the same
    #    category set.
    #
    # 2. User has NOT set category in configuration. Then the json
    #    files must all have the category set. The categories can be
    #    different.
    #
    # Go through and make sure there aren't any problems with
    # categories.

    api = slumber.API(api_url)

    # Build a dict of cat title -> cat data.
    all_categories = api.category.get()
    all_categories = dict([(cat['title'], cat)
                           for cat in all_categories['objects']])

    try:
        category = cfg.get('project', 'category')
        category = category.strip()
        if category not in all_categories:
            steve.err('Category "%s" does not exist on server. Build it there '
                      'first.' % category)
            return 1

    except ConfigParser.NoOptionError:
        category = None

    errors = False
    for fn, contents in data:
        if not category:
            this_cat = contents.get('category')
            if not this_cat:
                steve.err('No category set in configuration and %s has no '
                          'category set.' % fn)
                errors = True
            elif this_cat != this_cat.strip():
                steve.err('Category "%s" has whitespace at beginning or '
                          'end.' % this_cat)
                return 1
            elif this_cat not in all_categories:
                steve.err('Category "%s" does not exist on server. '
                          'Build it there first.' % this_cat)
                return 1

        else:
            this_cat = contents.get('category')
            if this_cat is not None and this_cat.strip() != category:
                steve.err('Category set in configuration (%s), but %s has '
                          'different category (%s).' % (
                        category, fn, this_cat))
                errors = True

    if errors:
        steve.err('Aborting.')
        return 1

    # Everything looks ok. So double-check with the user and push.

    steve.out('Pushing to:    %s' % api_url)
    steve.out('Using api_key: %s' % api_key)
    steve.out('Once you push, you can not undo it. Push for realz? Y/N')
    if not raw_input().strip().lower().startswith('y'):
        steve.err('Aborting.')
        return 1

    for fn, contents in data:
        contents['category'] = category or contents.get('category')

        # FIXME - check to see if video exists and if so, update it
        # instead.
        if contents.get('id') is not None:
            steve.out('Updating %s "%s" (%s)' % (
                    contents['id'], contents['title'], fn))
            vid = api.video(contents['id']).put(
                contents, username=username, api_key=api_key)
        else:
            steve.out('Pushing "%s" (%s)' % (contents['title'], fn))
            vid = api.video.post(contents, username=username, api_key=api_key)
            contents['id'] = vid['id']
            steve.out('   Now has id %s' % vid['id'])

        steve.save_json_file(cfg, fn, contents)

    return 0


def main(argv):
    parser = steve.BetterArgumentParser(
        byline=BYLINE,
        description=steve.wrap_paragraphs(
            'steve makes it easier to aggregate and edit metadata for videos '
            'for a richard instance.'
            '\n\n'
            'This program comes with ABSOLUTELY NO WARRANTY.  '
            'This is free software and you are welcome to redistribute it'
            'under the terms of the GPLv3.'),
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        default=False,
        help='runs steve quietly--only prints errors')

    # parser.add_argument(
    #     '--debug',
    #     action='store_true',
    #     default=False,
    #     help='runs steve in debug mode--no sending email.')

    subparsers = parser.add_subparsers(
        title='Commands',
        help='Run "%(prog)s CMD --help" for additional help')

    createproject_parser = subparsers.add_parser(
        'createproject', help='creates a new project')
    createproject_parser.add_argument(
        'directory',
        help='name/path for the project directory')
    createproject_parser.set_defaults(func=createproject_cmd)

    fetch_parser = subparsers.add_parser(
        'fetch', help='fetches all the videos and generates .json files')
    fetch_parser.set_defaults(func=fetch_cmd)

    status_parser = subparsers.add_parser(
        'status', help='shows you status of the videos in this project')
    status_parser.add_argument(
        '--list',
        action='store_true',
        default=False,
        help='lists files one per line with no other output')
    status_parser.set_defaults(func=status_cmd)

    scrapevideo_parser = subparsers.add_parser(
        'scrapevideo', help='fetches metadata for a video from a site')
    scrapevideo_parser.add_argument(
        'video',
        nargs=1)
    scrapevideo_parser.set_defaults(func=scrapevideo_cmd)

    push_parser = subparsers.add_parser(
        'push', help='pushes metadata to a richard instance')
    push_parser.add_argument(
        '--apikey',
        help='pass in your API key via the command line')
    push_parser.set_defaults(func=push_cmd)

    parsed = parser.parse_args(argv)

    return parsed.func(parser, parsed)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
