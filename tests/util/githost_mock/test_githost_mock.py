# coding: utf-8

import tempfile
from unittest import TestCase

from tests.util.cmd import cmd
from tests.util.githost_mock import GitHostMock


class TestGitHostMock(TestCase):
    def test_start_and_stop(self):
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
