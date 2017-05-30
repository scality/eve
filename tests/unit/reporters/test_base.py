"""
Test module for the eve.reporters.base module.

This module will test functions and classes nested in the eve.reporter.base
module.


Attributes:
    FAILED_BUILD (dict): Module level dictionary which is used as a failed
    build fixture for status push related tests.
    SUCCEEDED_BUILD (dict): Module level dictionary which is used as a
    succeeded build fixture for status push related tests
"""
from eve.reporters import base
from twisted.internet import defer
from twisted.trial import unittest

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

SUCCEEDED_BUILD = {
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


class TestBaseBuildStatusPush(unittest.TestCase):
    def test_constructor(self):
        """Test the __init__ method of the BaseBuildStatusPush class."""
        ctx = base.BaseBuildStatusPush(name='foo')
        self.assertIsNotNone(ctx)


class TestHipChatBuildStatusPush(unittest.TestCase):
    def test_constructor(self):
        """Test the __init__ method of the HipChatBuildStatusPush class."""
        ctx = base.HipChatBuildStatusPush(room_id='foo', token='bar')
        self.assertEquals(ctx.room_id, 'foo')
        self.assertEquals(ctx.token, 'bar')

    def test_add_tag(self):
        """Test the addTag method of the HipChatBuildStatusPush class."""
        ctx = base.HipChatBuildStatusPush(room_id='foo', token='bar')
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

    def test_filterBuilds(self):
        """Test the filterBuilds method of the HipChatBuildStatusPush class."""
        ctx = base.HipChatBuildStatusPush(room_id='foo', token='bar')
        ctx.builders = None
        self.assertTrue(ctx.filterBuilds(SUCCEEDED_BUILD))

    @defer.inlineCallbacks
    def test_send(self):
        """Test the send method of the HipChatBuildStatusPush class."""
        ctx = base.HipChatBuildStatusPush(room_id='foo', token='bar')
        with self.assertRaises(AttributeError):
            yield ctx.send(SUCCEEDED_BUILD)

        with self.assertRaises(AttributeError):
            yield ctx.send(FAILED_BUILD)


class TestBitbucketBuildStatusPush(unittest.TestCase):
    def test_constructor(self):
        """Test the __init__ method of the BitbucketBuildStatusPush class."""
        build_status = base.BitbucketBuildStatusPush(
            login='foo', password='bar')
        self.assertIsNotNone(build_status)

    def test_gather_data(self):
        """Test the gather_data method of the BitbucketBuildStatusPush class.
        """
        build_status = base.BitbucketBuildStatusPush(
            login='foo', password='bar')
        data = build_status.gather_data(SUCCEEDED_BUILD)
        self.assertEquals(data, ('pre-merge', 0, 'build #1',
                                 '(SUCCESS) build #1 on ring:master [success]',
                                 'Hooray!'))

    def test_forge_url(self):
        """Test the forge_url method of the BitbucketBuildStatusPush class."""
        build_status = base.BitbucketBuildStatusPush(
            login='foo', password='bar')
        build_status.gather_data(SUCCEEDED_BUILD)
        url = build_status.forge_url(SUCCEEDED_BUILD)
        self.assertEquals(url, ('https://api.bitbucket.org/2.0/repositories/'
                                'scality/ring/commit/cafebabe/statuses/build'))
        base.BitbucketBuildStatusPush.base_url = 'https://localhost:12345'
        url = build_status.forge_url(SUCCEEDED_BUILD)
        self.assertEquals(url, ('https://localhost:12345/2.0/repositories/'
                                'scality/ring/commit/cafebabe/statuses/build'))
