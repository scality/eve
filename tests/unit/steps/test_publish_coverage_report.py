"""Unit tests of `eve.steps.public_coverage_report`."""

import unittest

import eve.steps.publish_coverage_report


class TestCodecovIOPublication(unittest.TestCase):
    def test_constructor(self):
        ctx = eve.steps.publish_coverage_report.CodecovIOPublication(
            'repository', 'revision', 'branch', 'name', 'flags')
        self.assertEquals(ctx.repository, 'repository')
        self.assertEquals(ctx.revision, 'revision')
        self.assertEquals(ctx.branch, 'branch')
        self.assertEquals(ctx.name, 'name')
        self.assertEquals(ctx.flags, 'flags')
