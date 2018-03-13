"""Unit tests of `eve.reporters.base`.

This module will test functions and classes in `eve.reporter.base`.

"""

from twisted.trial import unittest

from eve.reporters.base import BaseBuildStatusPush


class TestBaseBuildStatusPush(unittest.TestCase):
    def test_init(self):
        ctx = BaseBuildStatusPush(name='foo')
        self.assertIsNotNone(ctx)
