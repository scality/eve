"""Unit tests of `eve.patch.worker_retry`.

This module simply test the different components of the
`eve.patch.worker_retry` module.

Here are the tested components :
    * `patch()` function

"""

from eve.patch.worker_retry import patch
from twisted.trial import unittest


class TestWorkerRetry(unittest.TestCase):
    def test_patch(self):
        """Test the patch function."""
        patch()
