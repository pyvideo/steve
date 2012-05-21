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
import sys
import os


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


def createproject_cmd(parsed):
    path = os.path.abspath(parsed.directory)
    if os.path.exists(path):
        steve.err('%s exists. Remove it and try again or try again with '
                  'a different filename.' % path)
        return 1

    # TODO: this kicks up errors. catch the errors and tell the user
    # something more useful
    os.makedirs(path)

    # TODO: create recipe file?

    steve.out('%s created.' % path)
    return 0


def main(argv):
    if '-q' not in argv and '--quiet' not in argv:
        steve.out(BYLINE)

    parser = argparse.ArgumentParser(
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

    return parsed.func(parsed)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
