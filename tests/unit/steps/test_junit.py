"""Unit tests of `eve.steps.junit`."""

import unittest

import eve.steps.junit


class TestJUnitShellCommand(unittest.TestCase):
    def test_init(self):
        ctx = eve.steps.junit.JUnitShellCommand(report_dir="foo")
        self.assertEquals(ctx.report_dir, "foo")
