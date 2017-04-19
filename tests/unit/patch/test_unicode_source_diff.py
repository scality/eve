"""Unit testing of the eve.patch.unicode_source_diff module.

This module simply test the different components of the
eve.patch.unicode_source_diff module. Here are the tested components :
    * patch() function

"""

from buildbot.process import buildrequest as bb_buildrequest
from eve.patch.unicode_source_diff import TempSourceStamp, patch
from twisted.trial import unittest


class TestUnicodeSourceDiff(unittest.TestCase):
    def test_patch(self):
        """Test that the patch() function in the eve.patch.unicode_source_diff
        module.

        The patch() function should patch the TempSourceStamp class exported
        by the buildbot.process.buildrequest module and replace it by
        the TempSourceStamp provided by the eve.patch.unicode_source_diff
        module.
        """
        patch()
        self.assertEquals(bb_buildrequest.TempSourceStamp, TempSourceStamp)


class TestTempSourceStamp(unittest.TestCase):
    """Unit test the TempSourceStamp class."""

    def test_asDict(self):
        """Test the asDict method of the TempSourceStamp class.

        Steps:
            - Instanciate TempSourceStamp
            - update its attributes
            - check that the asDict method return value
        """
        ctx = TempSourceStamp()
        ctx.ssid = 'foo'
        ctx.changes = 'bar'
        ctx.patch = ('foo', 'bar', 'baz')
        ctx.patch_info = ('Author', 'Comment')
        self.assertEquals(ctx.asDict(), {
            'patch_comment': 'Comment',
            'patch_level': 'foo',
            'patch_body': 'bar',
            'patch_author': 'Author',
            'patch_subdir': 'baz'
        })

        ctx.patch = None
        self.assertEquals(ctx.asDict(), {
            'patch_comment': 'Comment',
            'patch_level': None,
            'patch_body': None,
            'patch_author': 'Author',
            'patch_subdir': None
        })
