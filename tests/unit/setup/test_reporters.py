import unittest

import eve.setup.reporters
from buildbot.plugins import util


class SetupReportersTest(unittest.TestCase):
    def test_hipchat_reporter(self):
        """Test the hipchat_reporter function."""
        util.env = util.load_env([
            ('DOCKER_BUILDER_NAME', 'foo'),
            ('HIPCHAT_ROOM', 'foo'),
            ('HIPCHAT_TOKEN', 'bar'),
            ('OPENSTACK_BUILDER_NAME', 'bar')
        ])
        self.assertIsNotNone(eve.setup.reporters.hipchat_reporter())

    def test_github_reporter(self):
        """Test the github_reporter function."""
        util.env = util.load_env([
            ('DOCKER_BUILDER_NAME', 'foo'),
            ('GITHUB_TOKEN', 'foo'),
            ('OPENSTACK_BUILDER_NAME', 'bar')
        ])
        self.assertIsNotNone(eve.setup.reporters.github_reporter())

    def test_bitbucket_reporter(self):
        """Test the bitbucket_reporter function."""
        util.env = util.load_env([
            ('DOCKER_BUILDER_NAME', 'foo'),
            ('EVE_GITHOST_LOGIN', 'foo'),
            ('EVE_GITHOST_PWD', 'bar'),
            ('OPENSTACK_BUILDER_NAME', 'bar')
        ])
        self.assertIsNotNone(eve.setup.reporters.bitbucket_reporter())
