import unittest

import eve.setup.schedulers
from buildbot.plugins import util


class SetupSchedulersTest(unittest.TestCase):
    def test_any_branch_scheduler(self):
        """Test the any_branch_scheduler function."""
        # yapf: disable
        util.env = util.load_env([
            ('BOOTSTRAP_BUILDER_NAME', ''),
            ('BOOTSTRAP_SCHEDULER_NAME', '')
        ])
        self.assertTrue(
            eve.setup.schedulers.any_branch_scheduler() is not None)

    def test_force_scheduler(self):
        """
        Test the force_scheduler function."""
        # yapf: disable
        util.env = util.load_env([
            ('BOOTSTRAP_BUILDER_NAME', 'foo'),
            ('GITCACHE_IN_USE', '0', int),
            ('GIT_OWNER', 'foo'),
            ('GIT_REPO', 'blblbl'),
            ('GIT_SLUG', 'bar'),
            ('FORCE_SCHEDULER_NAME', 'bar'),
            ('FORCE_BUILD_PARAM_COUNT', '0', int)
        ])
        self.assertTrue(eve.setup.schedulers.force_scheduler() is not None)

    def test_try_scheduler(self):
        """Test the try_scheduler function."""
        # yapf: disable
        util.env = util.load_env([
            ('BOOTSTRAP_BUILDER_NAME', 'foo'),
            ('TRY_SCHEDULER_NAME', 'foo'),
            ('TRY_PWD', 'bar'),
            ('TRY_PORT', '12345'),
        ])
        self.assertTrue(eve.setup.schedulers.try_scheduler() is not None)

    def test_triggerable_scheduler(self):
        """Test the triggerable_scheduler function."""
        self.assertTrue(
            eve.setup.schedulers.triggerable_scheduler('foo', 'bar')
            is not None)
