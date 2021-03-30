"""Unit tests of `eve.steps.public_coverage_report`."""

import unittest

import eve.steps.publish_coverage_report


class TestCodecovIOPublication(unittest.TestCase):
    def test_init(self):
        ctx = eve.steps.publish_coverage_report.CodecovIOPublication(
            'repository', 'revision', 'branch', 'name', 'flags')
        self.assertEqual(ctx.repository, 'repository')
        self.assertEqual(ctx.revision, 'revision')
        self.assertEqual(ctx.branch, 'branch')
        self.assertEqual(ctx.name, 'name')
        self.assertEqual(ctx.flags, 'flags')
