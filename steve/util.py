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
import datetime
import json
import sys
import textwrap


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


def out(*output, **kwargs):
    """Writes output to stdout.

    :arg wrap: If you set ``wrap=False``, then ``out`` won't textwrap
        the output.

    """
    output = ' '.join([str(o) for o in output])
    if kwargs.get('wrap') != False:
        output = '\n'.join(wrap(output, kwargs.get('indent', '')))
    elif kwargs.get('indent'):
        indent = kwargs['indent']
        output = indent + ('\n' + indent).join(output.splitlines())
    sys.stdout.write(output + '\n')
