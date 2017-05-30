"""Unit tests of `eve.setup.boostrap`.

Attributes:
    DumbWorker (namedtuple): structure to define a fake buildbot worker for
        bootstrap tests.

"""

import collections
import unittest

import eve.setup.bootstrap
from buildbot.plugins import util

DumbWorker = collections.namedtuple('DumbWorker', ['name'])


class TestBootstrap(unittest.TestCase):
    def setUp(self):
        """Set up a random environment for maximum code coverage."""
        util.env = util.load_env([
            ('ARTIFACTS_URL', ''),
            ('ARTIFACTS_PREFIX', 'foo_'),
            ('BOOTSTRAP_BUILDER_NAME', 'foo'),
            ('DOCKER_BUILDER_NAME', 'foo'),
            ('GIT_HOST', 'foo'),
            ('GIT_OWNER', 'bar'),
            ('GIT_SLUG', 'slug/repo'),
            ('GIT_CACHE_HOST', 'foo'),
            ('GIT_CACHE_PORT', '11111', int),
            ('GIT_REPO', 'foo/bar.git'),
            ('GITCACHE_IN_USE', '0', int),
            ('MASTER_START_TIME', '9999'),
            ('PATCHER_FILE_PATH', ''),
            ('PROJECT_YAML', ''),
            ('RAX_LOGIN', 'foo'),
            ('RAX_PWD', 'bar'),
        ])

    def test_bootstrap_builder(self):
        builder_config = eve.setup.bootstrap.bootstrap_builder(
            [DumbWorker(name='foo')])
        self.assertEquals(len(builder_config.factory.steps), 10)
