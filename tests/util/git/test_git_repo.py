from unittest import TestCase

from tests.util.cmd import cmd
from tests.util.git.git_repo import RemoteGitRepo
from tests.util.yaml_factory import SingleCommandYaml


class TestGitRepo(TestCase):
    def test_git_repo(self):
        remote = RemoteGitRepo()
        local = remote.clone()
        command = 'do something'
        branch = 'feature/1'
        local.push(SingleCommandYaml(command), branch=branch)
        assert command in cmd('cat eve/main.yml', cwd=local._dir)
        assert branch in cmd('git branch', cwd=remote._dir)
