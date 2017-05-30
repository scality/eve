"""Unit tests of `eve.scripts.runner`."""

import eve.scripts.runner
from twisted.trial import unittest


class TestScriptRunner(unittest.TestCase):
    def test_main(self):
        """Test that the main function is runs and raises SystemExit."""
        with self.assertRaises(SystemExit):
            eve.scripts.runner.main()
