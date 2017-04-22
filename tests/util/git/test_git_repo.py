import tempfile
from unittest import TestCase

from tests.util.cmd import cmd
from tests.util.git.git_repo import LocalGitRepo
from tests.util.yaml_factory import SingleCommandYaml


class TestGitRepo(TestCase):
    def test_git_repo(self):
        """
        Steps:
            - create a fake remote git repo
            - clone it with the LocalGitRepo class
            - push a specified yaml file on a specified branch
            - check that the file is on that branch
            - check the branch has been pushed to the remote
        """
        remote = tempfile.mkdtemp(prefix='eve_remote_')
        cmd('git init --bare', cwd=remote)
        local = LocalGitRepo(remote=remote)
        command = 'do something'
        branch = 'feature/1'
        local.push(SingleCommandYaml(command), branch=branch)
        assert command in cmd('cat eve/main.yml', cwd=local._dir)
        assert branch in cmd('git branch', cwd=local._dir)
        assert branch in cmd('git branch', cwd=remote)
