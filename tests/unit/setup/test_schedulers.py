"""Unit tests of `eve.setup.schedulers`."""

import unittest

from buildbot.plugins import util

import eve.setup.schedulers


class TestSetupSchedulers(unittest.TestCase):
    def test_any_branch_scheduler(self):
        util.env = util.load_env([
            ('BOOTSTRAP_BUILDER_NAME', ''),
            ('BOOTSTRAP_SCHEDULER_NAME', '')
        ])
        self.assertIsNotNone(eve.setup.schedulers.any_branch_scheduler())

    def test_force_scheduler(self):
        util.env = util.load_env([
            ('BOOTSTRAP_BUILDER_NAME', 'foo'),
            ('FORCE_SCHEDULER_NAME', 'bar'),
            ('FORCE_BUILD_PARAM_COUNT', '0', int),
            ('GIT_OWNER', 'foo'),
            ('GIT_REPO', 'blblbl'),
            ('GIT_SLUG', 'bar'),
        ])
        self.assertIsNotNone(eve.setup.schedulers.force_scheduler())

    def test_prolong_scheduler(self):
        util.env = util.load_env([
            ('BOOTSTRAP_BUILDER_NAME', 'foo'),
            ('FORCE_BUILD_PARAM_COUNT', '0', int),
            ('GIT_OWNER', 'foo'),
            ('GIT_REPO', 'blblbl'),
            ('GIT_SLUG', 'bar'),
            ('PROLONG_SCHEDULER_NAME', 'bar'),
        ])
        self.assertIsNotNone(eve.setup.schedulers.prolong_scheduler())

    def test_promote_scheduler(self):
        util.env = util.load_env([
            ('BOOTSTRAP_BUILDER_NAME', 'foo'),
            ('FORCE_BUILD_PARAM_COUNT', '0', int),
            ('GIT_OWNER', 'foo'),
            ('GIT_REPO', 'blblbl'),
            ('GIT_SLUG', 'bar'),
            ('PROMOTE_SCHEDULER_NAME', 'bar'),
        ])
        self.assertIsNotNone(eve.setup.schedulers.promote_scheduler())

    def test_try_scheduler(self):
        util.env = util.load_env([
            ('BOOTSTRAP_BUILDER_NAME', 'foo'),
            ('TRY_SCHEDULER_NAME', 'foo'),
            ('TRY_PWD', 'bar'),
            ('TRY_PORT', '12345'),
        ])
        self.assertIsNotNone(eve.setup.schedulers.try_scheduler())

    def test_triggerable_scheduler(self):
        self.assertIsNotNone(eve.setup.schedulers.triggerable_scheduler('foo',
                                                                        'bar'))
