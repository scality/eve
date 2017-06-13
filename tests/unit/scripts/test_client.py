"""Unit tests of `eve.scripts.client`."""

from twisted.trial import unittest

import eve.scripts.client


class TestClient(unittest.TestCase):
    def test_main(self):
        """Test that `main()` runs without throwing an exception.

        Steps:
            - launch the main function.
            - catch the SystemExit exception.

        """
        with self.assertRaises(SystemExit):
            eve.scripts.client.main()

    def test_output(self):
        """Test that `output()` runs without throwing an exception."""
        eve.scripts.client.output("foo", "bar")
