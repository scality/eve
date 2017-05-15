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
"""Create and interact with a local git repository."""

from __future__ import print_function

import shutil
import tempfile
from os import mkdir
from os.path import basename, join
from uuid import uuid4

from tests.util.cmd import cmd
from tests.util.yaml_factory import RawYaml, SingleCommandYaml


class LocalGitRepo(object):
    def __init__(self, remote):
        self.remote = remote
        self._dir = tempfile.mkdtemp(prefix='eve_local_')
        cmd('git clone {} .'.format(self.remote), cwd=self._dir)
        cmd('git config user.email "john.doe@example.com"', cwd=self._dir)
        cmd('git config user.name "John Doe"', cwd=self._dir)
        self.branch = None

    def push(self, yaml=None, dirs=(), branch=None):
        """Create a new commit to trigger a test build.

        Args:
            yaml (YamlFactory or str): The yaml file to be pushed.
            dirs (list): Additional folders to be pushed to the git repo root.
            branch (str): The branch name to push to.

        """
        if branch is None:
            branch = 'bugfix/heal_the_world_{}'.format(uuid4())
        if yaml is None:
            yaml = SingleCommandYaml()

        self.branch = branch
        cmd('git checkout -b %s' % branch, cwd=self._dir)

        mkdir(join(self._dir, 'eve'))
        if isinstance(yaml, RawYaml):
            yaml.filedump(join(self._dir, 'eve', 'main.yml'))
        else:
            shutil.copyfile(yaml, join(self._dir, 'eve', 'main.yml'))

        for src in dirs:
            shutil.copytree(src, join(self._dir, basename(src)))

        cmd('git add -A', cwd=self._dir)
        cmd('git commit -m "add yaml file"', cwd=self._dir)
        cmd('git push -u origin HEAD:%s' % branch, cwd=self._dir)
        return self

    @property
    def loglines(self):
        """Return a list of loglines from the git log command.

        Returns:
            list: The lines resulting from git log command
                `git log --pretty=format:"%an %ae|%s|%H|%cd" --date=iso`.

        """
        res = cmd(
            'git log --pretty=format:"%an %ae|%s|%H|%cd" --date=iso',
            cwd=self._dir)
        return reversed(res.splitlines())

    def cmd(self, *args, **kwargs):
        """Run a command in the git repo directory."""
        kwargs['cwd'] = self._dir
        return cmd(*args, **kwargs)
