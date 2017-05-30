"""Unit tests of `eve.scripts.runner`."""

import eve.scripts.runner
from twisted.trial import unittest


class TestRunner(unittest.TestCase):
    def test_main(self):
        """Test that `main()` raises SystemExit."""
        with self.assertRaises(SystemExit):
            eve.scripts.runner.main()
