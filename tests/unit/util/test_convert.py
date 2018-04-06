"""Unit test of `eve.util.convert`."""

import unittest

from eve.util.convert import convert_to_bytes, convert_to_cpus


class TestConversion(unittest.TestCase):
    def test_convert_to_bytes(self):
        with self.assertRaises(ValueError):
            convert_to_bytes('notanumber')
        self.assertEquals(convert_to_bytes('1234'), 1234)
        self.assertEquals(convert_to_bytes('1B'), 1)
        self.assertEquals(convert_to_bytes('1b'), 1)
        self.assertEquals(convert_to_bytes('2K'), 2048)
        self.assertEquals(convert_to_bytes('2k'), 2048)
        self.assertEquals(convert_to_bytes('4M'), 4194304)
        self.assertEquals(convert_to_bytes('4m'), 4194304)
        self.assertEquals(convert_to_bytes('8G'), 8589934592)
        self.assertEquals(convert_to_bytes('8g'), 8589934592)
        self.assertEquals(convert_to_bytes('8gi'), 8589934592)
        self.assertEquals(convert_to_bytes('8gb'), 8589934592)

    def test_convert_to_cpus(self):
        with self.assertRaises(ValueError):
            convert_to_cpus('notanumber')
        with self.assertRaises(ValueError):
            convert_to_cpus('100M')
        with self.assertRaises(ValueError):
            convert_to_cpus('100a')
        self.assertEquals(convert_to_cpus('123'), 123)
        self.assertEquals(convert_to_cpus('0.100'), 0.1)
        self.assertEquals(convert_to_cpus('3.14'), 3.14)
        self.assertEquals(convert_to_cpus('100m'), 0.1)
        self.assertEquals(convert_to_cpus('123m'), 0.123)
        self.assertEquals(convert_to_cpus('0.1m'), 0.0001)
        self.assertEquals(convert_to_cpus('3.14m'), 0.00314)
