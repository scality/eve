"""Unit tests of `eve.util.step`."""

import unittest

from buildbot.plugins import util
from buildbot.process.results import FAILURE, SKIPPED, SUCCESS, WARNINGS

from eve.util.step import (hideStepIf, hideStepIfSkipped, hideStepIfSuccess,
                           hideStepIfSuccessOrSkipped)


class Test(unittest.TestCase):
    def setUp(self):
        self.recall = util.env.get('HIDE_INTERNAL_STEPS', None)
        if not self.recall:
            util.env['HIDE_INTERNAL_STEPS'] = 1

    def tearDown(self):
        if self.recall:
            util.env.HIDE_INTERNAL_STEPS = self.recall
        else:
            util.env.pop('HIDE_INTERNAL_STEPS')

    def test_hideStepIf(self):
        util.env.HIDE_INTERNAL_STEPS = 1
        self.assertEqual(hideStepIf(SUCCESS, [SUCCESS]), True)
        self.assertEqual(hideStepIf(FAILURE, [SUCCESS]), False)
        self.assertEqual(hideStepIf(WARNINGS, [FAILURE]), False)
        self.assertEqual(hideStepIf(SKIPPED, [SUCCESS, SKIPPED]), True)

        util.env.HIDE_INTERNAL_STEPS = 0
        self.assertEqual(hideStepIf(SUCCESS, [SUCCESS]), False)
        self.assertEqual(hideStepIf(FAILURE, [SUCCESS]), False)
        self.assertEqual(hideStepIf(WARNINGS, [FAILURE]), False)
        self.assertEqual(hideStepIf(SKIPPED, [SUCCESS, SKIPPED]), False)

    def test_hideStepIfSuccess(self):
        util.env.HIDE_INTERNAL_STEPS = 1
        self.assertEqual(hideStepIfSuccess(SUCCESS, None), True)
        self.assertEqual(hideStepIfSuccess(SKIPPED, None), False)
        self.assertEqual(hideStepIfSuccess(FAILURE, None), False)

        util.env.HIDE_INTERNAL_STEPS = 0
        self.assertEqual(hideStepIfSuccess(SUCCESS, None), False)
        self.assertEqual(hideStepIfSuccess(SKIPPED, None), False)
        self.assertEqual(hideStepIfSuccess(FAILURE, None), False)

    def test_hideStepIfSkipped(self):
        util.env.HIDE_INTERNAL_STEPS = 1
        self.assertEqual(hideStepIfSkipped(SKIPPED, None), True)
        self.assertEqual(hideStepIfSkipped(SUCCESS, None), False)
        self.assertEqual(hideStepIfSkipped(FAILURE, None), False)

        util.env.HIDE_INTERNAL_STEPS = 0
        self.assertEqual(hideStepIfSkipped(SKIPPED, None), False)
        self.assertEqual(hideStepIfSkipped(SUCCESS, None), False)
        self.assertEqual(hideStepIfSkipped(FAILURE, None), False)

    def test_hideStepIfSuccessOrSkipped(self):
        util.env.HIDE_INTERNAL_STEPS = 1
        self.assertEqual(hideStepIfSuccessOrSkipped(SUCCESS, None), True)
        self.assertEqual(hideStepIfSuccessOrSkipped(SKIPPED, None), True)
        self.assertEqual(hideStepIfSuccessOrSkipped(FAILURE, None), False)

        util.env.HIDE_INTERNAL_STEPS = 0
        self.assertEqual(hideStepIfSuccessOrSkipped(SUCCESS, None), False)
        self.assertEqual(hideStepIfSuccessOrSkipped(SKIPPED, None), False)
        self.assertEqual(hideStepIfSuccessOrSkipped(FAILURE, None), False)
