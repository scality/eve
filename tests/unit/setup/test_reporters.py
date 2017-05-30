"""Unit tests of `eve.setup.reporters`."""

import unittest

import eve.setup.reporters
from buildbot.plugins import util


class TestSetupReporters(unittest.TestCase):
    def test_hipchat_reporter(self):
        util.env = util.load_env([
            ('DOCKER_BUILDER_NAME', 'foo'),
            ('HIPCHAT_ROOM', 'foo'),
            ('HIPCHAT_TOKEN', 'bar'),
            ('OPENSTACK_BUILDER_NAME', 'bar')
        ])
        self.assertIsNotNone(eve.setup.reporters.hipchat_reporter())

    def test_github_reporter(self):
        util.env = util.load_env([
            ('DOCKER_BUILDER_NAME', 'foo'),
            ('GITHUB_TOKEN', 'foo'),
            ('OPENSTACK_BUILDER_NAME', 'bar')
        ])
        self.assertIsNotNone(eve.setup.reporters.github_reporter())

    def test_bitbucket_reporter(self):
        util.env = util.load_env([
            ('DOCKER_BUILDER_NAME', 'foo'),
            ('EVE_GITHOST_LOGIN', 'foo'),
            ('EVE_GITHOST_PWD', 'bar'),
            ('OPENSTACK_BUILDER_NAME', 'bar')
        ])
        self.assertIsNotNone(eve.setup.reporters.bitbucket_reporter())
