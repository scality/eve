"""This test suite checks end-to-end operation of EVE."""
import os
import unittest

from tests.util.cluster import Cluster
from tests.util.yaml_factory import SingleCommandYaml


def need_env_vars(varnames, reason):
    """Decorator to skip test if environment variables are not passsed."""
    return unittest.skipIf(
        any([varname not in os.environ for varname in varnames]), reason)


def need_rackspace_credentials(reason='needs rackspace credentials'):
    """Decorator to skip test if rackspace credentials are not passed."""
    return need_env_vars(['RAX_LOGIN', 'RAX_PWD'], reason)


def need_artifacts_credentials(reason='needs artifacts credentials'):
    """Decorator to skip test if artifacts credentials are not passed."""
    return need_env_vars(['ARTIFACTS_URL', 'SECRET_ARTIFACT_CREDS'], reason)


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cluster = Cluster().start()

    @classmethod
    def tearDownClass(cls):
        cls.cluster.stop()
        del cls.cluster

    def setUp(self):
        self.local_repo = self.cluster.clone()

    def test_artifacts_properties(self):
        """Tests that artifacts properties are well set.
        """
        self.local_repo.push(yaml=SingleCommandYaml('exit 0'))
        buildset = self.cluster.force(self.local_repo.branch)
        assert buildset.result == 'success'

        build = buildset.buildrequest.build
        child_buildsets = build.children
        assert len(child_buildsets) == 1
        child_build = child_buildsets[0].buildrequest.build
        assert child_build.result == 'success'

        short_hash = self.local_repo.cmd('git rev-parse --short HEAD')
        timestamp = self.local_repo.cmd('git log -1 --format=%cd '
                                        '--date="format-local:%y%m%d%H%M%S"')

        expected = 'mock:repo_owner:test:staging-0.0.0.r{}.{}.pre-merge.' \
                   '00000001'.format(timestamp.strip(), short_hash.strip())
        assert child_build.properties['artifacts_name'][0] == expected

        # TODO: pass a fake env variable and test
        expected = 'None/' + expected
        assert child_build.properties['artifacts_public_url'][0] == expected
