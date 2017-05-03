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
"""GitHostMock Daemon."""

from __future__ import print_function

import os

from tests.util.cmd import cmd
from tests.util.daemon import Daemon


class GitHostMock(Daemon):
    _post_start_delay = 1

    def __init__(self):
        """Githost mock object to mimic Github/Bitbucket using git-daemon."""
        self.port = self.get_free_port()
        super(GitHostMock, self).__init__(name='githost_{}'.format(self.port))
        self._start_cmd = [
            'git', 'daemon', '--reuseaddr', '--export-all',
            '--enable=receive-pack',
            '--base-path={}'.format(self._base_path),
            '--port={}'.format(self.port)
        ]  # yapf: disable

    def pre_start_hook(self):
        """Create a bare git repo before starting the git daemon."""
        repo_path = os.path.join(self._base_path, 'repo_owner', 'test.git')
        cmd('mkdir -p {}'.format(repo_path), cwd=self._base_path)
        cmd('git init --bare', cwd=repo_path)
