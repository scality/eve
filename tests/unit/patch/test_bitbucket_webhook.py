"""Unit testing of the eve.patch.bitbucket_webhook module.

This module simply test the different components of the
eve.patch.bitbucket_webhook module. Here are the tested components :
    * patch() function

"""
import eve.patch.bitbucket_webhook
from buildbot.www.hooks import bitbucket as bb_hooks
from twisted.trial import unittest


class TestBitbucketWebhook(unittest.TestCase):
    def test_patch(self):
        """Test the patch function in the eve.patch.bitbucket_webhook
        module.

        The patch function should patch the getChanges function exported
        by the buildbot.www.hooks module and replace it by the getChanges
        function provided by the eve.patch.bitbucket_webhook module.
        """
        eve.patch.bitbucket_webhook.patch()
        self.assertEquals(bb_hooks.getChanges,
                          eve.patch.bitbucket_webhook.getChanges)
