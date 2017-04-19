# coding: utf-8
"""This test suite checks end-to-end operation of EVE."""

from __future__ import print_function

import shutil
import tempfile
from os.path import join
from uuid import uuid4

from tests.util.cmd import cmd
from tests.util.yaml_factory import SingleCommandYaml, YamlFactory


class GitRepo(object):
    pass


class RemoteGitRepo(GitRepo):
    def __init__(self, url=None):
        if url is None:
            self._dir = tempfile.mkdtemp(prefix='eve_remote_')
            cmd('git init --bare', cwd=self._dir)
        else:
            self._dir = url

    def clone(self):
        return LocalGitRepo(remote=self._dir)

    @property
    def url(self):
        return self._dir

    def __delete__(self, instance):
        pass


class LocalGitRepo(GitRepo):
    def __init__(self, remote):
        self.remote = remote
        self._dir = tempfile.mkdtemp(prefix='eve_local_')
        cmd('git clone {} .'.format(self.remote), cwd=self._dir)
        cmd('git config user.email "john.doe@example.com"', cwd=self._dir)
        cmd('git config user.name "John Doe"', cwd=self._dir)
        self.branch = None

    def push(self, yaml=None, branch=None):
        """Create a new commit to trigger a test build.

        Args:
            eve_dir (str): directory of the yaml test file.
        """
        if branch is None:
            branch = 'bugfix/heal_the_world_{}'.format(uuid4())
        if yaml is None:
            yaml = SingleCommandYaml()

        self.branch = branch
        cmd('git checkout -b %s' % branch, cwd=self._dir)

        src_ctxt = join('tests', 'system', 'contexts')
        shutil.copytree(src_ctxt, join(self._dir, 'eve'))

        if isinstance(yaml, YamlFactory):
            yaml.filedump(join(self._dir, 'eve', 'main.yml'))
        else:
            shutil.copyfile(yaml, join(self._dir, 'eve', 'main.yml'))
        cmd('git add -A', cwd=self._dir)
        cmd('git commit -m "add yaml file"', cwd=self._dir)
        cmd('git push -u origin HEAD:%s' % branch, cwd=self._dir)
        return self

    @property
    def loglines(self):
        res = cmd(
            'git log --pretty=format:"%an %ae|%s|%H|%cd" --date=iso',
            cwd=self._dir)
        return reversed(res.splitlines())

    def cmd(self, *args, **kwargs):
        kwargs['cwd'] = self._dir
        return cmd(*args, **kwargs)

    def __delete__(self, instance):
        pass
