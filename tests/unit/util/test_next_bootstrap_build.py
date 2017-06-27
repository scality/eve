"""Unit tests of `eve.util.next_bootstrap_build`."""

import unittest
from collections import namedtuple

from buildbot.plugins import util

Source = namedtuple('MockSource', 'branch')
Request = namedtuple('MockRequest', 'source')


class TestNextBootstrapBuild(unittest.TestCase):

    def setUp(self):
        self.requests = [
            Request(Source('development/4.3')),
            Request(Source('feature/foo')),
            Request(Source('feature/bar')),
            Request(Source('development/5.1')),
            Request(Source('bugfix/spam')),
            Request(Source('development/5.1')),
            Request(Source('feature/baz')),
            Request(Source('bugfix/egg')),
            Request(Source('bugfix/bacon')),
            Request(Source('improvement/cool')),
        ]
        self.recall = util.env.get('LOW_PRIORITY_BRANCH', None)
        if not self.recall:
            util.env['LOW_PRIORITY_BRANCH'] = ''

    def tearDown(self):
        if self.recall:
            util.env.LOW_PRIORITY_BRANCH = self.recall
        else:
            util.env.pop('LOW_PRIORITY_BRANCH')

    def test_no_low_priority(self):
        util.env.LOW_PRIORITY_BRANCH = ''
        self.assertEqual(util.nextBootstrapBuild('', self.requests),
                         self.requests[0])

    def test_first_is_low(self):
        util.env.LOW_PRIORITY_BRANCH = '^development/'
        self.assertEqual(util.nextBootstrapBuild('', self.requests),
                         self.requests[1])

    def test_four_first_are_low(self):
        util.env.LOW_PRIORITY_BRANCH = '^(development|feature)/'
        self.assertEqual(util.nextBootstrapBuild('', self.requests),
                         self.requests[4])

    def test_low_priority_behind(self):
        util.env.LOW_PRIORITY_BRANCH = '^bugfix/'
        self.assertEqual(util.nextBootstrapBuild('', self.requests),
                         self.requests[0])
