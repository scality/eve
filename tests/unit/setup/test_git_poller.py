import unittest

import eve.setup.git_poller
from buildbot.plugins import util


class SetupGitPollerTest(unittest.TestCase):
    def setUp(self):
        util.env = util.load_env([
            ('GIT_POLLING', 'foo'),
            ('GIT_REPO', ''),
        ])

    def test_git_poller(self):
        """
        Test that the git_poller function is run without throwing an exception
        and that it returns something different than None.
        """
        self.assertTrue(eve.setup.git_poller.git_poller() is not None)
