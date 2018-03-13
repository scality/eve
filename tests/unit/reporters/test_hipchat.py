"""Unit tests of `eve.reporters.hipchat`.

This module will test functions and classes in `eve.reporter.hipchat`.

Attributes:
    FAILED_BUILD (dict): Module level dictionary which is used as a failed
        build fixture for status push related tests.
    SUCCEEDED_BUILD (dict): Module level dictionary which is used as a
        succeeded build fixture for status push related tests.

"""

from twisted.internet import defer
from twisted.trial import unittest

from eve.reporters.hipchat import HipChatBuildStatusPush

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

SUCCEEDED_PREMERGE_BUILD = {
    'buildid': 1,
    'state_string': 'SUCCESS',
    'results': 0,
    'url': 'baz',
    'complete_at': 10,
    'started_at': 1,
    'properties': {
        'stage_name': ['pre-merge']
    },
    'buildset': {
        'sourcestamps': [{
            'repository': 'scality/ring.git',
            'branch': 'master',
            'revision': 'cafebabe',
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


class TestHipChatBuildStatusPush(unittest.TestCase):
    def test_init(self):
        ctx = HipChatBuildStatusPush('post-merge', room_id='foo',
                                     token='bar')
        self.assertEquals(ctx.room_id, 'foo')
        self.assertEquals(ctx.token, 'bar')

    def test_add_tag(self):
        ctx = HipChatBuildStatusPush('post-merge', room_id='foo',
                                     token='bar')
        ctx.add_tag('foo', 'bar', 'baz', color='green')
        self.assertEquals(ctx.attributes[0], {
            'label': 'foo',
            'value': {
                'label': 'bar',
                'style': 'lozenge-success',
                'icon': {
                    'url': 'baz'
                }
            }
        })

    def test_filterBuilds_premerge(self):
        ctx = HipChatBuildStatusPush('post-merge', room_id='foo',
                                     token='bar')
        ctx.builders = None
        self.assertFalse(ctx.filterBuilds(SUCCEEDED_PREMERGE_BUILD))

    def test_filterBuilds_postmerge(self):
        ctx = HipChatBuildStatusPush('post-merge', room_id='foo',
                                     token='bar')
        ctx.builders = None
        self.assertTrue(ctx.filterBuilds(SUCCEEDED_POSTMERGE_BUILD))

    @defer.inlineCallbacks
    def test_send(self):
        ctx = HipChatBuildStatusPush('post-merge', room_id='foo',
                                     token='bar')
        with self.assertRaises(AttributeError):
            yield ctx.send(SUCCEEDED_POSTMERGE_BUILD)

        with self.assertRaises(AttributeError):
            yield ctx.send(FAILED_BUILD)
