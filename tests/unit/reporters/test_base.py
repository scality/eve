"""Unit tests of `eve.reporters.base`.

This module will test functions and classes in `eve.reporter.base`.

"""

from buildbot.process.results import (CANCELLED, EXCEPTION, FAILURE, RETRY,
                                      SKIPPED, SUCCESS, WARNINGS)
from twisted.trial import unittest

from eve.reporters.base import BaseBuildStatusPush

BUILD = {
    'buildid': 1,
    'builder': {
        'name': 'pre-merge'
    },
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

    def test_filter_bootstrap_builds(self):
        bootstrap_build = BUILD

        ctx = BaseBuildStatusPush(name='foo')
        bootstrap_build['properties']['reason'] = ['branch updated']
        bootstrap_build['builder']['name'] = 'bootstrap'

        # Ensure there's no report when bootstrap results isn't notify worthy
        bootstrap_build['results'] = SUCCESS
        self.assertFalse(ctx.filterBuilds(bootstrap_build))
        bootstrap_build['results'] = None
        self.assertFalse(ctx.filterBuilds(bootstrap_build))
        bootstrap_build['results'] = RETRY
        self.assertFalse(ctx.filterBuilds(bootstrap_build))

        # Ensure there's a report when bootstrap results is notify worthy
        bootstrap_build['results'] = SKIPPED
        self.assertTrue(ctx.filterBuilds(bootstrap_build))
        bootstrap_build['results'] = CANCELLED
        self.assertTrue(ctx.filterBuilds(bootstrap_build))
        bootstrap_build['results'] = WARNINGS
        self.assertTrue(ctx.filterBuilds(bootstrap_build))
        bootstrap_build['results'] = EXCEPTION
        self.assertTrue(ctx.filterBuilds(bootstrap_build))
        bootstrap_build['results'] = FAILURE
        self.assertTrue(ctx.filterBuilds(bootstrap_build))
