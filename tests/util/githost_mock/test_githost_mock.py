# Copyright 2017 Scality
#
# This file is part of Eve.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.
"""Test the GitHostMock daemon."""

import tempfile
from unittest import TestCase

from tests.util.cmd import cmd
from tests.util.githost_mock import GitHostMock


class TestGitHostMock(TestCase):
    def test_start_and_stop(self):
        """Test start and stop a githost mock daemon.

        Steps:
            - Start a GitHostMock.
            - Clone it to a temp directory.
            - Create a branch and push it.
            - Check that the branch has been pushed successfully.
            - Stop the GitHostMock.

        """
        ghm = GitHostMock().start()
        clone_dir = tempfile.mkdtemp()
        cmd(
            'git clone git://localhost:{}/repo_owner/test.git .'.format(
                ghm.port),
            cwd=clone_dir)
        cmd('git config user.email "john.doe@example.com"', cwd=clone_dir)
        cmd('git config user.name "John Doe"', cwd=clone_dir)
        cmd('echo hello > readme.txt', cwd=clone_dir)
        cmd('git add -A', cwd=clone_dir)
        cmd('git commit -m "add yaml file"', cwd=clone_dir)
        cmd('git push -u origin HEAD:mybranch', cwd=clone_dir)
        assert 'set up to track remote branch mybranch' in \
               cmd('git checkout mybranch', cwd=clone_dir)
        ghm.stop()
