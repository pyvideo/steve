import os
from unittest import TestCase

from click.testing import CliRunner
import pytest

from steve.cmdline import cli


# helpful for testing command line stuff
#
# http://click.pocoo.org/5/testing/#basic-testing
# http://click.pocoo.org/5/testing/#file-system-isolation


class CmdlineHelpTestCase(TestCase):
    def test_help(self):
        """Basic test to make sure the cli works"""
        runner = CliRunner()
        result = runner.invoke(cli, ())
        assert result.exit_code == 0
        assert 'Usage' in result.output.splitlines()[0]


class CreateprojectTestCase(TestCase):
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ('createproject', '--help'))
        assert result.exit_code == 0

    def test_basic(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            path = os.getcwd()

            result = runner.invoke(cli, ('createproject', 'testprj'))
            assert result.exit_code == 0
            assert os.path.exists(os.path.join(path, 'testprj', 'steve.ini'))

    def test_directory_already_exists(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            path = os.getcwd()

            # Create the project directory
            testprjpath = os.path.join(path, 'testprj')
            os.makedirs(testprjpath)

            result = runner.invoke(cli, ('createproject', 'testprj'))
            assert result.exit_code == 1
            assert '{0} exists.'.format(os.path.join(path, 'testprj')) in result.output


class FetchTestCase(TestCase):
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ('fetch', '--help'))
        assert result.exit_code == 0

    # FIXME: More extensive tests


class PullTestCase(TestCase):
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ('pull', '--help'))
        assert result.exit_code == 0

    # FIXME: More extensive tests


class PushTestCase(TestCase):
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ('push', '--help'))
        assert result.exit_code == 0

    # FIXME: More extensive tests


class ScrapevideoTestCase(TestCase):
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ('scrapevideo', '--help'))
        assert result.exit_code == 0

    # FIXME: More extensive tests


class StatusTestCase:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ('status', '--help'))
        assert result.exit_code == 0

    # FIXME: More extensive tests


class VerifyTestCase:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ('verify', '--help'))
        assert result.exit_code == 0

    # FIXME: More extensive tests


class WebeditTestCase:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ('webedit', '--help'))
        assert result.exit_code == 0

    # FIXME: More extensive tests
