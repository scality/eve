"""Unit tests of `eve.setup.git_poller`."""

import unittest

import eve.setup.git_poller
from buildbot.plugins import util


class TestSetupGitPoller(unittest.TestCase):
    def setUp(self):
        util.env = util.load_env([
            ('GIT_POLLING', 'foo'),
            ('GIT_REPO', ''),
        ])

    def test_git_poller(self):
        self.assertIsNotNone(eve.setup.git_poller.git_poller())
