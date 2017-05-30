"""Unit tests of `eve.scripts.client`."""

import eve.scripts.client
from twisted.trial import unittest


class TestClient(unittest.TestCase):
    def test_main(self):
        """
        Test that the main() function is run without throwing an exception.

        Steps:
            - launch the main function
            - catch the SystemExit exception
        """
        with self.assertRaises(SystemExit):
            eve.scripts.client.main()

    def test_output(self):
        """
        Test that the output function is run without throwing an exception.
        """
        eve.scripts.client.output("foo", "bar")
