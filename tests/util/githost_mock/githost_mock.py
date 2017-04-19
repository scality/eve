# coding: utf-8
"""This test suite checks end-to-end operation of EVE."""

from __future__ import print_function

import os

from tests.util.cmd import cmd
from tests.util.daemon import Daemon


class GitHostMock(Daemon):
    _post_start_delay = 1

    def __init__(self):
        self.port = self.get_free_port()
        super(GitHostMock, self).__init__(name='githost_{}'.format(self.port))
        self._start_cmd = [
            'git', 'daemon', '--reuseaddr', '--export-all',
            '--enable=receive-pack',
            '--base-path={}'.format(self._base_path),
            '--port={}'.format(self.port)
        ]  # yapf: disable

    def pre_start_hook(self):
        repo_path = os.path.join(self._base_path, 'repo_owner', 'test.git')
        cmd('mkdir -p {}'.format(repo_path), cwd=self._base_path)
        cmd('git init --bare', cwd=repo_path)
