#######################################################################
# This file is part of steve.
#
# Copyright (C) 2012-2014 Will Kahn-Greene
# Licensed under the Simplified BSD License. See LICENSE for full
# license.
#######################################################################

import ConfigParser
import json
import os
import sys
import unicodedata

import argparse
import blessings
import vidscraper

try:
    import steve
except ImportError:
    sys.stderr.write(
        'The steve library is not on your sys.path.  Please install steve.\n')
    sys.exit(1)

import steve.restapi
import steve.richardapi
from steve.util import (
    BetterArgumentParser,
    ConfigNotFound,
    YOUTUBE_EMBED,
    convert_to_json,
    err,
    generate_filename,
    get_from_config,
    get_project_config,
    load_json_files,
    out,
    save_json_file,
    save_json_files,
    scrapevideo,
    verify_json_files,
    vidscraper_to_dict,
    with_config,
    wrap_paragraphs,
)
from steve.webedit import serve


BYLINE = ('steve-cmd: {0} ({1}).'.format(steve.__version__,
                                         steve.__releasedate__))

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


def createproject_cmd(parser, parsed, args):
    if not parsed.quiet:
        parser.print_byline()

    path = os.path.abspath(parsed.directory)
    if os.path.exists(path):
        err('{0} exists. Remove it and try again or try again with '
            'a different filename.'.format(path))
        return 1

    # TODO: this kicks up errors. catch the errors and tell the user
    # something more useful
    out('Creating directory {0}...'.format(path))
    os.makedirs(path)

    out('Creating steve.ini...')
    f = open(os.path.join(path, 'steve.ini'), 'w')
    f.write(CONFIG)
    f.close()

    out('{0} created.'.format(path))
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

    out('Scraping {0}...'.format(url))
    video_feed = vidscraper.auto_feed(url)
    video_feed.load()

    print 'Found {0} videos...'.format(video_feed.video_count)
    for i, video in enumerate(video_feed):
        filename = generate_filename(video.title or '')
        filename = '{index:04d}_{basename}.json'.format(
            index=i, basename=filename[:40])

        print 'Working on {0}... ({1})'.format(
            unicodedata.normalize('NFKD', video.title).encode(
                'ascii', 'ignore'),
            filename)
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
                out(u'{0}: {1}'.format(fn, term.bold(whiteboard)),
                    wrap=False)

        if done_files:
            out('')
            for fn in done_files:
                out('{0}: {1}'.format(fn, term.bold(term.green('Done!'))),
                    wrap=False)

        out('')
        out('In progress: {0:3d}'.format(len(in_progress_files)))
        out('Done:        {0:3d}'.format(len(done_files)))

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
                out('  - {0}'.format(error))

    out('Done!')
    return 0


def scrapevideo_cmd(parser, parsed, args):
    if not parsed.quiet:
        parser.print_byline()

    video_url = parsed.video[0]
    data = scrapevideo(video_url, parsed.richard, 'object')
    if parsed.save:
        cfg = get_project_config()

        projectpath = cfg.get('project', 'projectpath')
        jsonpath = os.path.join(projectpath, 'json')

        if not os.path.exists(jsonpath):
            os.makedirs(jsonpath)

        fn = 'json/' + generate_filename(data['title']) + '.json'

        if os.path.exists(fn):
            err('It already exists!')
            return 1

        with open(fn, 'w') as fp:
            fp.write(convert_to_json(data))
        print 'Saved as {0}'.format(fn)
    else:
        print convert_to_json(data)
    return 0


@with_config
def push_cmd(cfg, parser, parsed, args):
    if not parsed.quiet:
        parser.print_byline()

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

    api = steve.restapi.API(api_url)

    all_categories = dict(
        [(cat['title'], cat)
         for cat in steve.richardapi.get_all_categories(api_url)])

    try:
        category = cfg.get('project', 'category')
        category = category.strip()
        if category not in all_categories:
            err('Category "{0}" does not exist on server. Build it there '
                'first.'.format(category))
            return 1
        else:
            out('Category {0} exists on site.'.format(category))
    except ConfigParser.NoOptionError:
        category = None

    errors = False
    for fn, contents in data:
        if category is None:
            this_cat = contents.get('category')
            if not this_cat:
                err('No category set in configuration and {0} has no '
                    'category set.'.format(fn))
                errors = True
            elif this_cat != this_cat.strip():
                err('Category "{0}" has whitespace at beginning or '
                    'end.'.format(this_cat))
                return 1
            elif this_cat not in all_categories:
                err('Category "{0}" does not exist on server. '
                    'Build it there first.'.format(this_cat))
                return 1

        else:
            this_cat = contents.get('category')
            if this_cat is not None and str(this_cat).strip() != category:
                err('Category set in configuration ({0}), but {1} has '
                    'different category ({2}).'.format(
                    category, fn, this_cat))
                errors = True

    if update:
        for fn, contents in data:
            if not 'id' in contents:
                err('id not in contents for "{0}".'.format(fn))
                errors = True
                break

    if errors:
        err('Aborting.')
        return 1

    # Everything looks ok. So double-check with the user and push.

    out('Pushing to: {0}'.format(api_url))
    out('Username:   {0}'.format(username))
    out('api_key:    {0}'.format(api_key))
    out('update?:    {0}'.format(update))
    out('Once you push, you can not undo it. Push for realz? Y/N')
    if not raw_input().strip().lower().startswith('y'):
        err('Aborting.')
        return 1

    for fn, contents in data:
        contents['category'] = category or contents.get('category')

        if not update:
            # Nix any id field since that causes problems.
            if 'id' in contents:
                if not parsed.overwrite:
                    print 'Skipping... already exists'
                    continue
                del contents['id']

            out('Pushing {0}'.format(fn))
            try:
                vid = steve.richardapi.create_video(api_url, api_key, contents)

                if 'id' in vid:
                    contents['id'] = vid['id']
                    out('   Now has id {0}'.format(vid['id']))
                else:
                    err('   Errors?: {0}'.format(vid))
            except steve.restapi.RestAPIException as exc:
                err('   Error?: {0}'.format(exc))
                err('   "{0}"'.format(exc.response.content))

        else:
            out('Updating {0} "{1}" ({2})'.format(
                contents['id'], contents['title'], fn))
            try:
                vid = steve.restapi.get_content(
                    api.video(str(contents['id'])).put(
                        contents, username=username, api_key=api_key))
            except steve.restapi.RestAPIException as exc:
                err('   Error?: {0}'.format(exc))
                err('   "{0}"'.format(exc.response.content))

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

    api = steve.restapi.API(api_url)

    all_categories = steve.restapi.get_content(
        api.category.get(username=username, api_key=api_key,
                         limit=0))
    cat = [cat_item for cat_item in all_categories['objects']
           if cat_item['title'] == cat_title]

    if not cat:
        err('Category "{0}" does not exist.'.format(cat_title))
        return 1

    # Get the category from the list of 1.
    cat = cat[0]

    out('Retrieved category.')

    data = []

    for counter, video_url in enumerate(cat['videos']):
        # Lame, but good enough for now.
        video_id = video_url.split('/')[-2]

        video_data = steve.restapi.get_content(
            api.video(video_id).get(username=username,
                                    api_key=api_key))

        out('Working on "{0}"'.format(video_data['slug']))

        # Nix some tastypie bits from the data.
        for bad_key in ('resource_uri',):
            if bad_key in video_data:
                del video_data[bad_key]

        # Add id.
        video_data['id'] = video_id

        fn = 'json/{0:4d}_{1}.json'.format(counter, video_data['slug'])
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
        '--richard',
        action='store_true',
        default=False,
        help='return richard JSON format')
    scrapevideo_parser.add_argument(
        '--save',
        action='store_true',
        default=False,
        help='saves it to the filesystem using the title as the filename')
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
    push_parser.add_argument(
        '--overwrite',
        action='store_true',
        default=False,
        help='if it exists, overwrite it')
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
