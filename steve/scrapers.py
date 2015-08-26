#######################################################################
# This file is part of steve.
#
# Copyright (C) 2012-2015 Will Kahn-Greene
# Licensed under the Simplified BSD License. See LICENSE for full
# license.
#######################################################################

import json
import subprocess
from datetime import datetime

from steve.util import is_youtube


class ScraperError(Exception):
    pass


class Scraper(object):
    def scrape(self, url):
        """Takes a url and returns list of dicts or None if not handled"""
        raise NotImplemented


class YoutubeScraper(object):
    def transform_item(self, item):
        """Converts youtube-dl output to richard fields"""
        return {
            'title': item['fulltitle'],
            'summary': item['description'],
            'description': '',
            'state': 2,  # Draft
            'category': '',
            'quality_notes': '',
            'language': '',
            'copyright_text': '',
            'thumbnail_url': item['thumbnail'],
            'duration': item['duration'],
            'source_url': item['webpage_url'],
            'whiteboard': '',
            'recorded': datetime.strptime(item['upload_date'], '%Y%m%d'),
            'slug': '',
            'tags': item['categories'],
            'speakers': []
        }

    def scrape(self, url):
        """Scrapes a url by passing it through youtube-dl"""
        if not is_youtube(url):
            return

        # FIXME: Sometimes youtube-dl takes a *long* time to run. This
        # needs to give indication of progress.
        try:
            output = subprocess.check_output(
                ['youtube-dl', '-j', url],
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as cpe:
            raise ScraperError('youtube-dl said "{0}".'.format(cpe.output))
        except OSError:
            raise ScraperError('youtube-dl not installed or not on PATH.')

        # Each line is a single JSON object.
        items = []
        for line in output.splitlines():
            items.append(json.loads(line))

        items = [self.transform_item(item) for item in items]

        return items
