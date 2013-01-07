#######################################################################
# This file is part of steve.
#
# Copyright (C) 2012, 2013 Will Kahn-Greene
# Licensed under the Simplified BSD License. See LICENSE for full
# license.
#######################################################################

import ConfigParser
import json
import os
import string
import sys

import argparse
import blessings
import slumber
import vidscraper
from slumber.exceptions import HttpServerError, HttpClientError

try:
    import steve
    from steve.util import (
        YOUTUBE_EMBED, with_config, BetterArgumentParser, wrap_paragraphs,
        out, err, vidscraper_to_dict, ConfigNotFound, convert_to_json,
        load_json_files, save_json_file, save_json_files, get_from_config,
        verify_json_files)
    from steve.webedit import serve
except ImportError:
    sys.stderr.write(
        'The steve library is not on your sys.path.  Please install steve.\n')
    sys.exit(1)


BYLINE = ('steve-cmd: %s (%s). ' % (steve.__version__, steve.__releasedate__))

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

# Your username and api key.
#
# Alternatively, you can pass this on the command line or put it in a
# separate API_KEY file which you can keep out of version control.
# e.g. username = willkg
#      api_key = OU812
# username =
# api_key =
"""

ALLOWED_LETTERS = string.ascii_letters + string.digits + '-_'


# FIXME: This is needed for steve to work, but it breaks Carl's stuff,
# but I'm not sure why.

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
        elif 500 <= resp.status_code <= 599:
            raise slumber.exceptions.HttpServerError(
                "Server Error %s" % resp.status_code,
                response=resp, content=resp.content)
        return resp.content
    slumber.Resource.post = post


def createproject_cmd(parser, parsed, args):
    if not parsed.quiet:
        parser.print_byline()

    path = os.path.abspath(parsed.directory)
    if os.path.exists(path):
        err('%s exists. Remove it and try again or try again with '
                  'a different filename.' % path)
        return 1

    # TODO: this kicks up errors. catch the errors and tell the user
    # something more useful
    out('Creating directory %s...' % path)
    os.makedirs(path)

    out('Creating steve.ini...')
    f = open(os.path.join(path, 'steve.ini'), 'w')
    f.write(CONFIG)
    f.close()

    out('%s created.' % path)
    out('')

    out('Now cd into the directory and edit the steve.ini file.')
    out('After you do that, you should put your project into version '
              'control. Srsly.')
    return 0


@with_config
def fetch_cmd(cfg, parser, parsed, args):
    if not parsed.quiet:
        parser.print_byline()

    projectpath = cfg.get('project', 'projectpath')
    jsonpath = os.path.join(projectpath, 'json')

    if not os.path.exists(jsonpath):
        os.makedirs(jsonpath)

    try:
        url = cfg.get('project', 'url')
    except ConfigParser.NoOptionError:
        url = ''

    if not url:
        err('url not specified in steve.ini project config file.')
        err('Add "url = ..." to [project] section of steve.ini file.')
        return 1

    if 'youtube' in url:
        try:
            youtube_embed = YOUTUBE_EMBED[cfg.get('project', 'youtube_embed')]
        except KeyError:
            err('youtube_embed must be either "iframe" or "object".')
            return 1
    else:
        youtube_embed = None

    out('Scraping %s...' % url)
    video_feed = vidscraper.auto_feed(url)
    video_feed.load()

    print 'Found %d videos...' % video_feed.video_count
    for i, video in enumerate(video_feed):
        if video.title:
            filename = video.title.replace(' ', '_')
            filename = ''.join([c for c in filename if c in ALLOWED_LETTERS])
            filename = '_' + filename
        else:
            filename = ''

        filename = '%04d%s.json' % (i, filename[:40])

        print 'Working on %s... (%s)' % (video.title, filename)
        item = vidscraper_to_dict(video, youtube_embed=youtube_embed)

        f = open(os.path.join('json', filename), 'w')
        f.write(convert_to_json(item))
        f.close()

        # TODO: what if there's a file there already? on the first one,
        # prompt the user whether to stomp on existing files or skip.
    return 0


@with_config
def status_cmd(cfg, parser, parsed, args):
    if not parsed.quiet and not parsed.list:
        parser.print_byline()

    if not parsed.list and not parsed.quiet:
        out('Video status:')
        out('')

    files = load_json_files(cfg)

    if not files:
        if not parsed.list:
            out('No files')
        return 0

    term = blessings.Terminal()

    done_files = []
    in_progress_files = []

    for fn, contents in files:
        whiteboard = contents.get('whiteboard', '')
        if whiteboard:
            in_progress_files.append((fn, whiteboard))
        else:
            done_files.append(fn)

    if parsed.list:
        for fn in in_progress_files:
            out(fn, wrap=False)

    else:
        if in_progress_files:
            for fn, whiteboard in in_progress_files:
                out(u'%s: %s' % (fn, term.bold(whiteboard)),
                    wrap=False)

        if done_files:
            out('')
            for fn in done_files:
                out('%s: %s' % (fn, term.bold(term.green('Done!'))),
                    wrap=False)

        out('')
        out('In progress: %3d' % len(in_progress_files))
        out('Done:        %3d' % len(done_files))

    return 0


@with_config
def verify_cmd(cfg, parser, parsed, args):
    if not parsed.quiet:
        parser.print_byline()

    files = load_json_files(cfg)
    if not files:
        out('No files')
        return 0

    filename_to_errors = verify_json_files(
        files, cfg.get('project', 'category'))
    for filename in sorted(filename_to_errors.keys()):
        errors = filename_to_errors[filename]
        if errors:
            out(filename)
            for error in errors:
                out('  - ' + error)

    out('Done!')
    return 0


def scrapevideo_cmd(parser, parsed, args):
    if not parsed.quiet:
        parser.print_byline()

    video_url = parsed.video[0]
    print json.dumps(steve.scrapevideo(video_url), indent=2, sort_keys=True)

    return 0


@with_config
def push_cmd(cfg, parser, parsed, args):
    if not parsed.quiet:
        parser.print_byline()

    # Monkeypatch slumber to suck less.
    monkeypatch_slumber()

    # Get username, api_url and api_key.

    username = get_from_config(cfg, 'username')
    api_url = get_from_config(cfg, 'api_url')

    update = parsed.update

    # Command line api_key overrides config-set api_key
    api_key = parsed.apikey
    if not api_key:
        try:
            api_key = cfg.get('project', 'api_key')
        except ConfigParser.NoOptionError:
            pass
    if not api_key:
        err('Specify an api key either in steve.ini, on command line, '
            'or in API_KEY file.')
        return 1

    if not username or not api_url or not api_key:
        return 1

    data = load_json_files(cfg)

    if args:
        data = [(fn, contents) for fn, contents in data if fn in args]

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
    all_categories = api.category.get(limit=0)
    all_categories = dict([(cat['title'], cat)
                           for cat in all_categories['objects']])

    try:
        category = cfg.get('project', 'category')
        category = category.strip()
        if category not in all_categories:
            err('Category "%s" does not exist on server. Build it there '
                      'first.' % category)
            return 1

    except ConfigParser.NoOptionError:
        category = None

    errors = False
    for fn, contents in data:
        if category is None:
            this_cat = contents.get('category')
            if not this_cat:
                err('No category set in configuration and %s has no '
                          'category set.' % fn)
                errors = True
            elif this_cat != this_cat.strip():
                err('Category "%s" has whitespace at beginning or '
                          'end.' % this_cat)
                return 1
            elif this_cat not in all_categories:
                err('Category "%s" does not exist on server. '
                          'Build it there first.' % this_cat)
                return 1

        else:
            this_cat = contents.get('category')
            if this_cat is not None and str(this_cat).strip() != category:
                err('Category set in configuration (%s), but %s has '
                          'different category (%s).' % (
                        category, fn, this_cat))
                errors = True

    if update:
        for fn, contents in data:
            if not 'id' in contents:
                err('id not in contents for "%s".' % fn)
                errors = True
                break

    if errors:
        err('Aborting.')
        return 1

    # Everything looks ok. So double-check with the user and push.

    out('Pushing to: %s' % api_url)
    out('Username:   %s' % username)
    out('api_key:    %s' % api_key)
    out('update?:    %s' % update)
    out('Once you push, you can not undo it. Push for realz? Y/N')
    if not raw_input().strip().lower().startswith('y'):
        err('Aborting.')
        return 1

    for fn, contents in data:
        contents['category'] = category or contents.get('category')

        if not update:
            # Nix any id field since that causes problems.
            if 'id' in contents:
                del contents['id']

            out('Pushing %s' % fn)
            try:
                vid = api.video.post(contents, username=username, api_key=api_key)
                if 'id' in vid:
                    contents['id'] = vid['id']
                    out('   Now has id %s' % vid['id'])
                else:
                    err('   Errors?: %s' % vid)
            except HttpClientError as exc:
                err('   ClientErrors?: %s' % exc)
                err('   "%s"' % exc.response.content)
            except HttpServerError as exc:
                err('   ServerErrors?: %s' % exc)

        else:
            out('Updating %s "%s" (%s)' % (
                    contents['id'], contents['title'], fn))
            try:
                vid = api.video(contents['id']).put(
                    contents, username=username, api_key=api_key)
            except HttpClientError as exc:
                err('   ClientErrors?: %s' % exc)
                err('   "%s"' % exc.response.content)
                raise
            except HttpServerError as exc:
                err('   ServerErrors?: %s' % exc)
                raise

        save_json_file(cfg, fn, contents)

    return 0


@with_config
def webedit_cmd(cfg, parser, parsed, args):
    parser.print_byline()
    serve()


@with_config
def pull_cmd(cfg, parser, parsed, args):
    if not parsed.quiet:
        parser.print_byline()

    username = get_from_config(cfg, 'username')
    api_url = get_from_config(cfg, 'api_url')
    cat_title = get_from_config(cfg, 'category')

    # Command line api_key overrides config-set api_key
    api_key = parsed.apikey
    if not api_key:
        try:
            api_key = cfg.get('project', 'api_key')
        except ConfigParser.NoOptionError:
            pass
    if not api_key:
        err('Specify an api key either in steve.ini, on command line, '
            'or in API_KEY file.')
        return 1

    if not username or not api_url or not cat_title or not api_key:
        return 1

    api = slumber.API(api_url)

    all_categories = api.category.get(username=username, api_key=api_key,
                                      limit=0)
    cat = [cat_item for cat_item in all_categories['objects']
           if cat_item['title'] == cat_title]

    if not cat:
        err('Category "%s" does not exist.' % cat_title)
        return 1

    # Get the category from the list of 1.
    cat = cat[0]

    out('Retrieved category.')

    data = []

    for counter, video_url in enumerate(cat['videos']):
        # Lame, but good enough for now.
        video_id = video_url.split('/')[-2]

        video_data = api.video(int(video_id)).get(username=username, api_key=api_key)

        out('Working on "%s"' % video_data['slug'])

        # Nix some tastypie bits from the data.
        for bad_key in ('resource_uri',):
            if bad_key in video_data:
                del video_data[bad_key]

        # Add id.
        video_data['id'] = video_id

        fn = 'json/%04d_%s.json' % (counter, video_data['slug'])
        data.append((fn, video_data))

    out('Saving files....')
    save_json_files(cfg, data)

    return 0


def main(argv):
    parser = BetterArgumentParser(
        byline=BYLINE,
        description=wrap_paragraphs(
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

    verify_parser = subparsers.add_parser(
        'verify', help='verifies json data')
    verify_parser.set_defaults(func=verify_cmd)

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
    push_parser.add_argument(
        '--update',
        action='store_true',
        default=False,
        help='update data rather than push new data (PUT vs. POST)')
    push_parser.set_defaults(func=push_cmd)

    pull_parser = subparsers.add_parser(
        'pull', help='pulls metadata from a richard instance')
    pull_parser.add_argument(
        '--apikey',
        help='pass in your API key via the command line')
    pull_parser.set_defaults(func=pull_cmd)

    webedit_parser = subparsers.add_parser(
        'webedit', help='launches web server so you can edit in browser')
    webedit_parser.set_defaults(func=webedit_cmd)

    parsed, args = parser.parse_known_args(argv)

    try:
        return parsed.func(parser, parsed, args)
    except ConfigNotFound as cnf:
        # Some commands have the @with_config decorator which throws a
        # ConfigNotFound exception if the steve.ini file can't be
        # found. Print the message and return 1.
        err(cnf.message)
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
