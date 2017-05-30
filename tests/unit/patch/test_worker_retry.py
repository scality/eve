"""Unit tests of `eve.patch.worker_retry`.

This module simply test the different components of the
`eve.patch.worker_retry` module.

Here are the tested components :
    * `patch()` function

"""

import buildbot.process.build
from eve.patch.worker_retry import patch
from twisted.trial import unittest


class TestPatchWorkerRetry(unittest.TestCase):
    def test_patch(self):
        FAILURE = buildbot.process.build.FAILURE
        patch()
        self.assertEqual(buildbot.process.build.RETRY, FAILURE)
        self.assertEqual(buildbot.process.build.FAILURE, FAILURE)
