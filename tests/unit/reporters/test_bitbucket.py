"""Unit tests of `eve.reporters.bitbucket`.

This module will test functions and classes in `eve.reporter.bitbucket`.

Attributes:
    SUCCEEDED_BUILD (dict): Module level dictionary which is used as a
        succeeded build fixture for status push related tests.

"""

from twisted.trial import unittest

from eve.reporters.bitbucket import BitbucketBuildStatusPush

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


class TestBitbucketBuildStatusPush(unittest.TestCase):
    def test_constructor(self):
        build_status = BitbucketBuildStatusPush(login='foo', password='bar')
        self.assertIsNotNone(build_status)

    def test_gather_data(self):
        build_status = BitbucketBuildStatusPush(login='foo', password='bar')
        data = build_status.gather_data(SUCCEEDED_PREMERGE_BUILD)
        self.assertEquals(data, ('pre-merge', 0, 'build #1',
                                 '(SUCCESS) build #1 on ring:master [success]',
                                 'Hooray!'))

    def test_forge_url(self):
        build_status = BitbucketBuildStatusPush(login='foo', password='bar')
        build_status.gather_data(SUCCEEDED_PREMERGE_BUILD)
        url = build_status.forge_url(SUCCEEDED_PREMERGE_BUILD)
        self.assertEquals(url, ('https://api.bitbucket.org/2.0/repositories/'
                                'scality/ring/commit/cafebabe/statuses/build'))
        BitbucketBuildStatusPush.base_url = 'https://localhost:12345'
        url = build_status.forge_url(SUCCEEDED_PREMERGE_BUILD)
        self.assertEquals(url, ('https://localhost:12345/2.0/repositories/'
                                'scality/ring/commit/cafebabe/statuses/build'))
