import eve.patch.worker_retry
from twisted.trial import unittest


class TestWorkerRetry(unittest.TestCase):
    def test_patch(self):
        """Test the patch function."""
        eve.patch.worker_retry.patch()
