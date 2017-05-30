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
        """Test the patch function in the eve.patch.bitbucket_webhook
        module.

        The patch function should patch the getChanges function exported
        by the buildbot.www.hooks module and replace it by the getChanges
        function provided by the eve.patch.bitbucket_webhook module.
        """
        patch()
        self.assertEquals(bb_hooks.getChanges, getChanges)
