"""Unit tests of `eve.setup.reporters`."""

import unittest

from buildbot.plugins import util

import eve.setup.reporters


class TestSetupReporters(unittest.TestCase):
    def test_hipchat_reporter(self):
        util.env = util.load_env([
            ('HIPCHAT_REPORTER_STAGE_FILTER', 'pre-merge'),
            ('HIPCHAT_ROOM', 'foo'),
            ('HIPCHAT_TOKEN', 'bar'),
        ])
        self.assertIsNotNone(eve.setup.reporters.hipchat_reporter([]))

    def test_github_reporter(self):
        util.env = util.load_env([
            ('GIT_HOST_REPORTER_STAGE_FILTER', ''),
            ('GITHUB_TOKEN', 'foo'),
        ])
        self.assertIsNotNone(eve.setup.reporters.github_reporter([]))

    def test_bitbucket_reporter(self):
        util.env = util.load_env([
            ('EVE_GITHOST_LOGIN', 'foo'),
            ('EVE_GITHOST_PWD', 'bar'),
            ('GIT_HOST_REPORTER_STAGE_FILTER', 'pre-merge;post-merge'),
        ])
        self.assertIsNotNone(eve.setup.reporters.bitbucket_reporter([]))

    def test_ultron_reporter(self):
        util.env = util.load_env([
            ('ULTRON_REPORTER_LOGIN', 'bar'),
            ('ULTRON_REPORTER_PWD', 'baz'),
            ('ULTRON_REPORTER_STAGE_FILTER', 'test;gotme'),
            ('ULTRON_REPORTER_URL', 'foo'),
        ])
        self.assertIsNotNone(eve.setup.reporters.ultron_reporter([]))
