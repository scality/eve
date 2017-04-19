# coding: utf-8
"""This test suite checks end-to-end operation of EVE."""
import unittest

from tests.util.cluster import Cluster
from tests.util.yaml_factory import EmptyYaml, SingleCommandYaml, ZeroStageYaml


class TestYamlSyntax(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cluster = Cluster().start()
        print cls.cluster.api.uri

    @classmethod
    def tearDownClass(cls):
        cls.cluster.stop()
        del cls.cluster

    def setUp(self):
        self.local_repo = self.cluster.clone()

    def tearDown(self):
        del self.local_repo

    def test_empty_yaml(self):
        """Tests builds triggered by git polling.

        Spawns EVE, sends a YAML that will fail and check that it fails.
        """
        self.local_repo.push(yaml=EmptyYaml())
        buildset = self.cluster.force(self.local_repo.branch)
        assert buildset.result == 'failure'

    def test_skip_if_no_branch_in_yml(self):
        """Tests that the build is cancelled when the branch is not covered
         by the eve/main.yml file
        """

        self.local_repo.push(yaml=ZeroStageYaml())
        buildset = self.cluster.force(self.local_repo.branch)
        assert buildset.result == 'cancelled'

    def test_simple_failure(self):
        """Tests builds triggered by git polling.

        Spawns EVE, sends a YAML that will fail and check that it fails.
        """
        self.local_repo.push(yaml=SingleCommandYaml('exit 1'))
        buildset = self.cluster.force(self.local_repo.branch)
        assert buildset.result == 'failure'

        build = buildset.buildrequest.build
        child_buildsets = build.children
        assert len(child_buildsets) == 1
        child_build = child_buildsets[0].buildrequest.build
        assert child_build.result == 'failure'

        failing_step = child_build.first_failing_step
        assert failing_step.state_string == "'exit 1' (failure)"

    def test_simple_success(self):
        """Tests builds triggered by git polling.

        Spawns EVE, sends a YAML that will fail and check that it fails.
        """
        self.local_repo.push(yaml=SingleCommandYaml('exit 0'))
        buildset = self.cluster.force(self.local_repo.branch)
        assert buildset.result == 'success'
        build = buildset.buildrequest.build
        child_buildsets = build.children
        assert len(child_buildsets) == 1
        child_build = child_buildsets[0].buildrequest.build
        assert child_build.result == 'success'
