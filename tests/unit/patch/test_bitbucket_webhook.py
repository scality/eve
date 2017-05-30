"""Unit tests of `eve.patch.bitbucket_webhook`.

This module simply test the different components of the
`eve.patch.bitbucket_webhook` module.

Here are the tested components :
    * `patch()` function

"""

from buildbot.www.hooks import bitbucket as bb_hooks
from eve.patch.bitbucket_webhook import getChanges, patch
from twisted.trial import unittest


class TestBitbucketWebhook(unittest.TestCase):
    def test_patch(self):
        """Test `patch()` properly monkeypatch the bitbucket webhook.

        The patch function should patch the `getChanges()` function exported
        by `buildbot.www.hooks` and replace it by the `getChanges()` function
        provided in `eve.patch.bitbucket_webhook`.

        """
        patch()
        self.assertEquals(bb_hooks.getChanges, getChanges)
