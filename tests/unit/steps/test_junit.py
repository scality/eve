import unittest

import eve.steps.junit


class TestJUnitShellCommand(unittest.TestCase):
    def test_constructor(self):
        """Test the __init__ method of the JUnitShellCommand class."""
        ctx = eve.steps.junit.JUnitShellCommand(report_dir="foo")
        self.assertEquals(ctx.report_dir, "foo")
