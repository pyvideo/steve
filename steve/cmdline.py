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
import json
import os
import string
import sys

import vidscraper

try:
    import steve
except ImportError:
    sys.stderr.write(
        'The steve library is not on your sys.path.  Please install steve.\n')
    sys.exit(1)


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
"""

YOUTUBE_EMBED = {
    'object': ('<object width="640" height="360"><param name="movie" '
               'value="%(youtubeurl)s?version=3&amp;hl=en_US"></param>'
               '<param name="allowFullScreen" value="true"></param>'
               '<param name="allowscriptaccess" value="always"></param>'
               '<embed src="%(youtubeurl)s?version=3&amp;hl=en_US" '
               'type="application/x-shockwave-flash" width="640" '
               'height="360" allowscriptaccess="always" '
               'allowfullscreen="true"></embed></object>'),
    'iframe': ('<iframe width="640" height="360" src="%(youtubeurl)s" '
               'frameborder="0" allowfullscreen></iframe>')
    }


ALLOWED_LETTERS = string.ascii_letters + string.digits + '-_'


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
    item['title'] = video.title
    item['summary'] = video.description
    item['description'] = u''
    item['tags'] = video.tags
    item['category'] = 0
    item['speakers'] = []
    item['quality_notes'] = u''
    item['copyright_text'] = video.license

    if 'youtube' in video.link:
        item['embed'] = youtube_embed % {'youtubeurl': video.link}
    else:
        item['embed'] = video.embed_code
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

    item['source_url'] = video.link
    item['whiteboard'] = u'needs editing'
    item['recorded'] = video.publish_datetime
    item['added'] = datetime.datetime.now()
    item['updates'] = datetime.datetime.now()
    item['slug'] = u''

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


def video_to_json(url, video, **kwargs):
    data = dict([(field, getattr(video, field))
                 for field in video.fields])

    for field in ('publish_datetime', 'file_url_expires'):
        dt = data.get(field, None)
        if isinstance(dt, datetime.datetime):
            data[field] = dt.isoformat()

    data['url'] = url
    if 'youtube.com' in url:
        data['object_embed_code'] = (YOUTUBE_EMBED['object'] %
                                     {'youtubeurl': url})
    return json.dumps(data, **kwargs)


def scrapevideo_cmd(parser, parsed):
    if not parsed.quiet:
        parser.print_byline()

    video_url = parsed.video[0]
    video_data = vidscraper.auto_scrape(video_url)
    print video_to_json(video_url, video_data, indent=2, sort_keys=True)

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

    # run_parser = subparsers.add_parser(
    #     'run', help='runs steve on the given configuration file')
    # run_parser.add_argument(
    #     'runconffile',
    #     help='name/path for the configuration file')
    # run_parser.set_defaults(func=run_cmd)

    # next6_parser = subparsers.add_parser(
    #     'next6', help='tells you next 6 dates for an event')
    # next6_parser.add_argument(
    #     'runconffile',
    #     help='name/path for the configuration file')
    # next6_parser.set_defaults(func=next6_cmd)

    parsed = parser.parse_args(argv)

    return parsed.func(parser, parsed)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
