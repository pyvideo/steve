# coding: utf-8

from __future__ import print_function

import os
import subprocess


class TestSteveCmd:
    def test_create_project(self, tmpdir, monkeypatch):
        # this changes to the temporary pytest directory and back after
        # the test has been run
        monkeypatch.chdir(tmpdir)
        proj = 'testprj'
        subprocess.check_output(['steve-cmd', 'createproject', proj])
        # you should be able to find the project from the last run with
        # find /tmp/pytest-current/
        # note the final "/" as this is a link to
        #   /tmp/pytest-NNN/test_create_project0
        assert os.path.exists(os.path.join(proj, 'steve.ini'))
