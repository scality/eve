"""Unit tests of `eve.setup.boostrap`.

Attributes:
    DumbWorker (namedtuple): structure to define a fake buildbot worker for
        bootstrap tests.

"""

import collections
import unittest

from buildbot.plugins import util

import eve.setup.bootstrap

DumbWorker = collections.namedtuple('DumbWorker', ['name'])


class TestBootstrap(unittest.TestCase):
    def setUp(self):
        """Set up a random environment for maximum code coverage."""
        util.env = util.load_env([
            ('ARTIFACTS_PREFIX', 'foo_'),
            ('BOOTSTRAP_BUILDER_NAME', 'foo'),
            ('DOCKER_BUILDER_NAME', 'foo'),
            ('GIT_HOST', 'foo'),
            ('GIT_OWNER', 'bar'),
            ('GIT_SLUG', 'slug/repo'),
            ('GIT_CACHE_HOST', 'foo'),
            ('GIT_CACHE_PORT', '11111', int),
            ('GIT_REPO', 'foo/bar.git'),
            ('MASTER_START_TIME', '9999'),
            ('MAX_STEP_DURATION', '1234'),
            ('MICROSERVICE_ARTIFACTS_IN_USE', '0', int),
            ('MICROSERVICE_GITCACHE_IN_USE', '0', int),
            ('PATCHER_FILE_PATH', ''),
            ('PROJECT_YAML', ''),
        ])

    def test_bootstrap_builder(self):
        builder_config = eve.setup.bootstrap.bootstrap_builder(
            [DumbWorker(name='foo')])
        self.assertEquals(len(builder_config.factory.steps), 5)
