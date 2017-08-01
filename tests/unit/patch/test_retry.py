"""Unit tests of `eve.patch.retry`.

This module simply test the different components of the
`eve.patch.retry` module.

Here are the tested components :
    * `patch()` function

"""

import buildbot.data.masters
from buildbot.process.results import CANCELLED
from twisted.trial import unittest

from eve.patch.retry import patch


class TestPatchWorkerRetry(unittest.TestCase):
    def test_patch(self):
        patch()
        self.assertEqual(buildbot.data.masters.RETRY, CANCELLED)
