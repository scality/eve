"""Unit tests of `eve.setup.reporters`."""

import unittest

from buildbot.plugins import util

import eve.setup.reporters


class TestSetupReporters(unittest.TestCase):
    def test_github_reporter(self):
        util.env = util.load_env([
            ('GITHUB_TOKEN', 'foo'),
        ])
        self.assertIsNotNone(eve.setup.reporters.github_reporter())

    def test_bitbucket_reporter(self):
        util.env = util.load_env([
            ('EVE_GITHOST_LOGIN', 'foo'),
            ('EVE_GITHOST_PWD', 'bar'),
        ])
        self.assertIsNotNone(eve.setup.reporters.bitbucket_reporter())
