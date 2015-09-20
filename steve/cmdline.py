#######################################################################
# This file is part of steve.
#
# Copyright (C) 2012-2014 Will Kahn-Greene
# Licensed under the Simplified BSD License. See LICENSE for full
# license.
#######################################################################

import ConfigParser
import os
import sys
import traceback

import click
import tabulate

from steve import __version__
import steve.restapi
import steve.richardapi
from steve.util import (
    ConfigNotFound,
    create_project_config_file,
    convert_to_json,
    generate_filename,
    get_from_config,
    get_project_config,
    get_project_config_file_name,
    get_video_id,
    load_json_files,
    save_json_file,
    save_json_files,
    scrape_video,
    scrape_videos,
    stringify,
    verify_json_files,
    with_config,
)
from steve.webedit import serve


BYLINE = ('steve-cmd: {0} ({1}).'.format(steve.__version__,
                                         steve.__releasedate__))

USAGE = '%prog [options] [command] [command-options]'
VERSION = 'steve ' + __version__

DESC = """
Command line interface for steve.
"""


def click_run():
    sys.excepthook = exception_handler
    try:
        cli(obj={})
    except ConfigNotFound as cnf:
        click.echo(VERSION)
        click.echo(cnf, err=True)


@click.group()
def cli():
    """Utility for aggregating and editing video metadata for a richard instance."""
    pass


@cli.command()
@click.option('--quiet/--no-quiet', default=False)
@click.argument('projectname', nargs=1)
@click.pass_context
def createproject(ctx, quiet, projectname):
    """Creates a new project."""
    if not quiet:
        click.echo(VERSION)

    path = os.path.abspath(projectname)
    if os.path.exists(path):
        raise click.ClickException(
            u'{0} exists. Remove it and try again or try again with '
            u'a different project name.'.format(path)
        )

    # TODO: this kicks up errors. catch the errors and tell the user
    # something more useful
    click.echo(u'Creating directory {0}...'.format(path))
    os.makedirs(path)

    conf_name = get_project_config_file_name()
    click.echo(u'Creating {0}...'.format(conf_name))
    create_project_config_file(path)

    click.echo(u'{0} created.'.format(path))
    click.echo(u'')

    click.echo(u'Now cd into the directory and edit the {0} file.'.format(conf_name))
    click.echo(u'After you do that, you should put your project into version '
               u'control. Srsly.')


@cli.command()
@click.option('--quiet/--no-quiet', default=False)
@click.option('--force/--no-force', default=False)
@click.pass_context
@with_config
def fetch(cfg, ctx, quiet, force):
    """Fetches videos and generates JSON files."""
    if not quiet:
        click.echo(VERSION)

    jsonpath = cfg.get('project', 'jsonpath')

    # source_url -> filename
    source_map = dict(
        (item['source_url'], fn)
        for fn, item in load_json_files(cfg)
    )

    if not os.path.exists(jsonpath):
        os.makedirs(jsonpath)

    try:
        url = cfg.get('project', 'url')
    except ConfigParser.NoOptionError:
        url = ''

    if not url:
        raise click.ClickException(
            u'url not specified in {0} project config file.\n\n'
            u'Add "url = ..." to [project] section of {0} file.'.format(
                get_project_config_file_name())
        )

    click.echo(u'Scraping {0}...'.format(url))
    click.echo(u'(This can take a *long* time with no indication of progress.)')
    videos = scrape_videos(url)

    click.echo(u'Found {0} videos...'.format(len(videos)))
    for i, video in enumerate(videos):
        if video['source_url'] in source_map and not force:
            click.echo(u'Skipping {0}... already exists.'.format(
                stringify(video['title'])))
            continue

        filename = generate_filename(video['title'])
        filename = '{index:04d}_{basename}.json'.format(
            index=i, basename=filename[:40])

        click.echo(u'Created {0}... ({1})'.format(
            stringify(video['title']), filename))

        with open(os.path.join(jsonpath, filename), 'w') as fp:
            fp.write(convert_to_json(video))

        # TODO: what if there's a file there already? on the first one,
        # prompt the user whether to stomp on existing files or skip.


@cli.command()
@click.option('--quiet/--no-quiet', default=False)
@click.option('--aslist/--no-aslist', default=False, help='Lists in-progress files one per line')
@click.pass_context
@with_config
def status(cfg, ctx, quiet, aslist):
    """Shows status for all videos in this project."""
    quiet = quiet or aslist
    if not quiet:
        click.echo(VERSION)
        click.echo('Video status:')
        click.echo()

    files = load_json_files(cfg)

    if not files:
        if not aslist:
            click.echo('No files')
        return

    done_files = []
    in_progress_files = []

    for fn, contents in files:
        whiteboard = contents.get('whiteboard', '')
        if whiteboard:
            in_progress_files.append((fn, whiteboard))
        else:
            done_files.append(fn)

    if aslist:
        for fn in in_progress_files:
            click.echo(fn)

    else:
        table = []
        if in_progress_files:
            for fn, whiteboard in in_progress_files:
                table.append([fn, whiteboard])

        if done_files:
            for fn in done_files:
                table.append([fn, 'Done!'])

        click.echo(tabulate.tabulate(table))
        click.echo()
        click.echo('In progress: {0:4d}'.format(len(in_progress_files)))
        click.echo('Done:        {0:4d}'.format(len(done_files)))


@cli.command()
@click.option('--quiet/--no-quiet', default=False)
@click.pass_context
@with_config
def verify(cfg, ctx, quiet):
    """Verifies JSON data."""
    if not quiet:
        click.echo(VERSION)

    files = load_json_files(cfg)
    if not files:
        click.echo('No files')
        return

    filename_to_errors = verify_json_files(
        files, cfg.get('project', 'category'))
    for filename in sorted(filename_to_errors.keys()):
        errors = filename_to_errors[filename]
        if errors:
            click.echo(filename)
            for error in errors:
                click.echo('  - {0}'.format(error))

    click.echo('Done!')


@cli.command()
@click.option('--quiet/--no-quiet', default=False)
@click.option('--save/--no-save', default=False,
              help='Save it to the filesystem using title as filename')
@click.argument('video_url', nargs=1)
@click.pass_context
def scrapevideo(ctx, quiet, save, video_url):
    """Fetches metadata for a video from a site."""
    if not quiet:
        click.echo(VERSION)

    data = scrape_video(video_url)[0]
    if save:
        cfg = get_project_config()

        jsonpath = cfg.get('project', 'jsonpath')

        if not os.path.exists(jsonpath):
            os.makedirs(jsonpath)

        fn = generate_filename(data['title']) + '.json'
        full_path = os.path.join(jsonpath, fn)

        if os.path.exists(fn):
            raise click.ClickException(u'File "%s" already exists!' % fn)

        with open(full_path, 'w') as fp:
            fp.write(convert_to_json(data))
        click.echo(u'Saved as {0}'.format(fn))

    else:
        click.echo(convert_to_json(data))


@cli.command()
@click.option('--quiet/--no-quiet', default=False)
@click.option('--apikey', default='', help='Pass in your API key via the command line')
@click.option('--update/--no-update', default=False,
              help='Update data rather than push new data (PUT vs. POST)')
@click.option('--overwrite/--no-overwrite', default=False, help='If it exists, overwrite it?')
@click.argument('files', nargs=-1)
@click.pass_context
@with_config
def push(cfg, ctx, quiet, apikey, update, overwrite, files):
    """Pushes metadata to a richard instance."""
    if not quiet:
        click.echo(VERSION)

    # Get username, api_url and api_key.

    username = get_from_config(cfg, 'username')
    api_url = get_from_config(cfg, 'api_url')

    # Command line api_key overrides config-set api_key
    if not apikey:
        try:
            apikey = cfg.get('project', 'api_key')
        except ConfigParser.NoOptionError:
            pass
    if not apikey:
        raise click.ClickException(
            u'Specify an api key either in {0}, on command line, '
            u'or in API_KEY file.'.format(get_project_config_file_name())
        )

    if not username or not api_url or not apikey:
        raise click.ClickException(u'Missing username, api_url or api_key.')

    data = load_json_files(cfg)

    if files:
        data = [(fn, contents) for fn, contents in data if fn in files]

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

    all_categories = dict(
        [(cat['title'], cat)
         for cat in steve.richardapi.get_all_categories(api_url)])

    try:
        category = cfg.get('project', 'category')
        category = category.strip()
        if category not in all_categories:
            raise click.ClickException(
                u'Category "{0}" does not exist on server. Build it there '
                u'first.'.format(category)
            )
        else:
            click.echo('Category {0} exists on site.'.format(category))
    except ConfigParser.NoOptionError:
        category = None

    errors = []
    for fn, contents in data:
        if category is None:
            this_cat = contents.get('category')
            if not this_cat:
                errors.append(
                    u'No category set in configuration and {0} has no '
                    u'category set.'.format(fn)
                )
            elif this_cat != this_cat.strip():
                errors.append(
                    u'Category "{0}" has whitespace at beginning or '
                    u'end.'.format(this_cat)
                )
            elif this_cat not in all_categories:
                errors.append(
                    u'Category "{0}" does not exist on server. '
                    u'Build it there first.'.format(this_cat)
                )

        else:
            this_cat = contents.get('category')
            if this_cat is not None and str(this_cat).strip() != category:
                errors.append(
                    u'Category set in configuration ({0}), but {1} has '
                    u'different category ({2}).'.format(category, fn, this_cat)
                )

    if update:
        for fn, contents in data:
            if 'id' not in contents:
                errors.append(
                    u'id not in contents for "{0}".'.format(fn)
                )

    if errors:
        raise click.ClickException('\n'.join(errors))

    # Everything looks ok. So double-check with the user and push.

    click.echo('Pushing to: {0}'.format(api_url))
    click.echo('Username:   {0}'.format(username))
    click.echo('api_key:    {0}'.format(apikey))
    click.echo('update?:    {0}'.format(update))
    click.echo('# videos:   {0}'.format(len(data)))
    click.echo('Once you push, you can not undo it. Push for realz? Y/N')
    if not raw_input().strip().lower().startswith('y'):
        raise click.Abort()

    for fn, contents in data:
        contents['category'] = category or contents.get('category')

        if not update:
            # Nix any id field since that causes problems.
            if 'id' in contents:
                if not overwrite:
                    click.echo(u'Skipping... already exists.')
                    continue
                del contents['id']

            click.echo('Pushing {0}'.format(fn))
            try:
                vid = steve.richardapi.create_video(api_url, apikey, contents)

                if 'id' in vid:
                    contents['id'] = vid['id']
                    click.echo('   Now has id {0}'.format(vid['id']))
                else:
                    click.echo('   Errors?: {0}'.format(vid), err=True)
            except steve.restapi.RestAPIException as exc:
                click.echo('   Error?: {0}'.format(exc), err=True)
                click.echo('   "{0}"'.format(exc.response.content), err=True)

        else:
            click.echo('Updating {0} "{1}" ({2})'.format(
                contents['id'], contents['title'], fn))
            try:
                vid = steve.richardapi.update_video(
                    api_url, apikey, contents['id'], contents)
            except steve.restapi.RestAPIException as exc:
                click.echo('   Error?: {0}'.format(exc), err=True)
                click.echo('   "{0}"'.format(exc.response.content), err=True)

        save_json_file(cfg, fn, contents)


@cli.command()
@click.pass_context
@with_config
def webedit(cfg, ctx):
    """Launches web server so you can edit in browser."""
    click.echo(VERSION)
    serve()


@cli.command()
@click.option('--quiet/--no-quiet', default=False)
@click.option('--apikey', default='', help='Pass in your API key via the command line')
@click.pass_context
@with_config
def pull(cfg, ctx, quiet, apikey):
    """Pulls data from a richard instance."""
    if not quiet:
        click.echo(VERSION)

    username = get_from_config(cfg, 'username')
    api_url = get_from_config(cfg, 'api_url')
    cat_title = get_from_config(cfg, 'category')

    # Command line api_key overrides config-set api_key
    if not apikey:
        try:
            apikey = cfg.get('project', 'api_key')
        except ConfigParser.NoOptionError:
            pass
    if not apikey:
        raise click.ClickException(
            u'Specify an api key either in {0}, on command line, '
            u'or in API_KEY file.'.format(get_project_config_file_name())
        )

    if not username or not api_url or not cat_title or not apikey:
        raise click.ClickException(u'Missing username, api_url or api_key.')

    api = steve.restapi.API(api_url)

    all_categories = steve.restapi.get_content(
        api.category.get(username=username, api_key=apikey,
                         limit=0))
    cat = [cat_item for cat_item in all_categories['objects']
           if cat_item['title'] == cat_title]

    if not cat:
        raise click.ClickException(u'Category "{0}" does not exist.'.format(cat_title))

    # Get the category from the list of 1.
    cat = cat[0]

    click.echo('Retrieved category.')

    data = []

    for counter, video_url in enumerate(cat['videos']):
        video_id = get_video_id(video_url)

        video_data = steve.restapi.get_content(
            api.video(video_id).get(username=username,
                                    api_key=apikey))

        click.echo('Working on "{0}"'.format(video_data['slug']))

        # Nix some tastypie bits from the data.
        for bad_key in ('resource_uri',):
            if bad_key in video_data:
                del video_data[bad_key]

        # Add id.
        video_data['id'] = video_id

        fn = 'json/{0:4d}_{1}.json'.format(counter, video_data['slug'])
        data.append((fn, video_data))

    click.echo('Saving files....')
    save_json_files(cfg, data)


def exception_handler(exc_type, exc_value, exc_tb):
    click.echo('Oh no! Steve has thrown an error while trying to do stuff.')
    click.echo()
    click.echo('Please write up a bug report with the specifics so that we can fix it.')
    click.echo()
    click.echo('https://github.com/pyvideo/steve/issues')
    click.echo()
    click.echo('Here is some information you can copy and paste into the bug report:')
    click.echo()
    click.echo('---')
    click.echo('Steve: ' + repr(__version__))
    click.echo('Python: ' + repr(sys.version))
    click.echo('Command line: ' + repr(sys.argv))
    click.echo(
        ''.join(traceback.format_exception(exc_type, exc_value, exc_tb)))
    click.echo('---')
