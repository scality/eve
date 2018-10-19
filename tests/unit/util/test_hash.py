"""Unit test of `eve.util.hash`."""

import unittest

from eve.util.hash import create_hash


class TestCreateHash(unittest.TestCase):
    def test_hash_creation(self):
        self.assertEqual(create_hash('toto', 'tata'),
                         'e8dcfdb2edac28d70770f4cae041b')
        self.assertEqual(create_hash('toto'), 'ef71dbe52628a3f83a77ab4948175')
        self.assertEqual(create_hash('worker-name', 'repository', 'stuff'),
                         'e4176fff953d613197728b96e0eb4')
