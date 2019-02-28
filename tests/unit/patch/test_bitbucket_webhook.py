"""Unit tests of `eve.patch.bitbucket_webhook`.

This module simply test the different components of the
`eve.patch.bitbucket_webhook` module.

Here are the tested components :
    * `patch()` function

"""

from buildbot.www.hooks.bitbucket import BitBucketHandler
from twisted.trial import unittest

from eve.patch.bitbucket_webhook import getChanges, patch


class TestBitbucketWebhook(unittest.TestCase):
    def test_patch(self):
        """Test `patch()` properly monkeypatch the bitbucket webhook.

        The patch function should patch the `getChanges()` function exported
        by `buildbot.www.hooks` and replace it by the `getChanges()` function
        provided in `eve.patch.bitbucket_webhook`.

        """
        patch()
        self.assertEquals(BitBucketHandler.getChanges, getChanges)
