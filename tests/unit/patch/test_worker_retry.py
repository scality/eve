"""Unit tests of `eve.patch.worker_retry`.

This module simply test the different components of the
`eve.patch.worker_retry` module.

Here are the tested components :
    * `patch()` function

"""

import eve.patch.worker_retry
from twisted.trial import unittest


class TestWorkerRetry(unittest.TestCase):
    def test_patch(self):
        """Test the patch function."""
        eve.patch.worker_retry.patch()
