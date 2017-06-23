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
        self.assertEquals(hideStepIf(SUCCESS, [SUCCESS]), True)
        self.assertEquals(hideStepIf(FAILURE, [SUCCESS]), False)
        self.assertEquals(hideStepIf(WARNINGS, [FAILURE]), False)
        self.assertEquals(hideStepIf(SKIPPED, [SUCCESS, SKIPPED]), True)

        util.env.HIDE_INTERNAL_STEPS = 0
        self.assertEquals(hideStepIf(SUCCESS, [SUCCESS]), False)
        self.assertEquals(hideStepIf(FAILURE, [SUCCESS]), False)
        self.assertEquals(hideStepIf(WARNINGS, [FAILURE]), False)
        self.assertEquals(hideStepIf(SKIPPED, [SUCCESS, SKIPPED]), False)

    def test_hideStepIfSuccess(self):
        util.env.HIDE_INTERNAL_STEPS = 1
        self.assertEquals(hideStepIfSuccess(SUCCESS, None), True)
        self.assertEquals(hideStepIfSuccess(SKIPPED, None), False)
        self.assertEquals(hideStepIfSuccess(FAILURE, None), False)

        util.env.HIDE_INTERNAL_STEPS = 0
        self.assertEquals(hideStepIfSuccess(SUCCESS, None), False)
        self.assertEquals(hideStepIfSuccess(SKIPPED, None), False)
        self.assertEquals(hideStepIfSuccess(FAILURE, None), False)

    def test_hideStepIfSkipped(self):
        util.env.HIDE_INTERNAL_STEPS = 1
        self.assertEquals(hideStepIfSkipped(SKIPPED, None), True)
        self.assertEquals(hideStepIfSkipped(SUCCESS, None), False)
        self.assertEquals(hideStepIfSkipped(FAILURE, None), False)

        util.env.HIDE_INTERNAL_STEPS = 0
        self.assertEquals(hideStepIfSkipped(SKIPPED, None), False)
        self.assertEquals(hideStepIfSkipped(SUCCESS, None), False)
        self.assertEquals(hideStepIfSkipped(FAILURE, None), False)

    def test_hideStepIfSuccessOrSkipped(self):
        util.env.HIDE_INTERNAL_STEPS = 1
        self.assertEquals(hideStepIfSuccessOrSkipped(SUCCESS, None), True)
        self.assertEquals(hideStepIfSuccessOrSkipped(SKIPPED, None), True)
        self.assertEquals(hideStepIfSuccessOrSkipped(FAILURE, None), False)

        util.env.HIDE_INTERNAL_STEPS = 0
        self.assertEquals(hideStepIfSuccessOrSkipped(SUCCESS, None), False)
        self.assertEquals(hideStepIfSuccessOrSkipped(SKIPPED, None), False)
        self.assertEquals(hideStepIfSuccessOrSkipped(FAILURE, None), False)
