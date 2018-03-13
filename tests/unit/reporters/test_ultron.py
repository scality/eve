"""Unit tests of `eve.reporters.ultron`.

This module will test functions and classes in `eve.reporter.ultron`.

Attributes:
    FAILED_BUILD (dict): Module level dictionary which is used as a failed
        build fixture for status push related tests.
    SUCCEEDED_BUILD (dict): Module level dictionary which is used as a
        succeeded build fixture for status push related tests.

"""

from twisted.internet import defer
from twisted.trial import unittest

from eve.reporters.ultron import UltronBuildStatusPush

FAILED_BUILD = {
    'buildid': 1,
    'state_string': 'FAILURE',
    'results': 0,
    'url': 'baz',
    'complete_at': 10,
    'started_at': 1,
    'properties': {
        'stage_name': ['pre-merge']
    },
    'buildset': {
        'sourcestamps': [{
            'repository': 'foo/bar.git',
            'branch': 'master',
        }]
    }
}

SUCCEEDED_POSTMERGE_BUILD = {
    'buildid': 1,
    'state_string': 'SUCCESS',
    'results': 0,
    'url': 'baz',
    'complete_at': 10,
    'started_at': 1,
    'properties': {
        'stage_name': ['post-merge']
    },
    'buildset': {
        'sourcestamps': [{
            'repository': 'scality/ring.git',
            'branch': 'master',
            'revision': 'cafebabe',
        }]
    }
}


class TestUltronBuildStatusPush(unittest.TestCase):
    def test_constructor(self):
        build_status = UltronBuildStatusPush(
            stages=['pre-merge', 'post-merge'],
            req_login='foo', req_password='bar',
            req_url='http://ultron.foo.baz/')
        self.assertIsNotNone(build_status)

    @defer.inlineCallbacks
    def test_send(self):
        ctx = UltronBuildStatusPush(stages='post-merge',
                                    req_login='foo',
                                    req_password='bar',
                                    req_url='http://ultron.foo.baz/')
        with self.assertRaises(AttributeError):
            yield ctx.send(SUCCEEDED_POSTMERGE_BUILD)

        with self.assertRaises(AttributeError):
            yield ctx.send(FAILED_BUILD)
