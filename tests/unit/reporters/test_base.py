"""Unit tests of `eve.reporters.base`.

This module will test functions and classes in `eve.reporter.base`.

"""

from twisted.trial import unittest

from eve.reporters.base import BaseBuildStatusPush

BUILD = {
    'buildid': 1,
    'state_string': 'SUCCESS',
    'results': 0,
    'url': 'baz',
    'complete_at': 10,
    'started_at': 1,
    'properties': {},
    'buildset': {
        'sourcestamps': [{
            'repository': 'scality/ring.git',
            'branch': 'master',
            'revision': 'cafebabe',
        }]
    }
}


class TestBaseBuildStatusPush(unittest.TestCase):
    def test_init(self):
        ctx = BaseBuildStatusPush(name='foo')
        self.assertIsNotNone(ctx)

    def test_filterBuilds(self):
        build = BUILD
        ctx = BaseBuildStatusPush(name='foo')

        build['properties']['reason'] = ['branch updated']
        self.assertFalse(ctx.filterBuilds(build))

        build['properties']['reason'] = ['foo (triggered by pre-merge)']
        self.assertFalse(ctx.filterBuilds(build))

        build['properties']['reason'] = ['foo (triggered by bootstrap)']
        self.assertTrue(ctx.filterBuilds(build))
