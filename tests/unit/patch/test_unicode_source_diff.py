"""Unit tests of `eve.patch.unicode_source_diff`.

This module simply test the different components of the
`eve.patch.unicode_source_diff` module.

Here are the tested components :
    * `patch()` function

"""

from buildbot.process import buildrequest as bb_buildrequest
from twisted.trial import unittest

from eve.patch.unicode_source_diff import TempSourceStamp, patch


class TestUnicodeSourceDiff(unittest.TestCase):
    def test_patch(self):
        """Test `patch()` properly monkeypatch `TempSourceStamp` class.

        The `patch()` function should patch the `TempSourceStamp` class
        exported by `buildbot.process.buildrequest` and replace it by
        the `TempSourceStamp` provided in `eve.patch.unicode_source_diff`.

        """
        patch()
        self.assertEquals(bb_buildrequest.TempSourceStamp, TempSourceStamp)


class TestTempSourceStamp(unittest.TestCase):
    def test_asDict(self):
        """Test the `asDict()` method of the `TempSourceStamp` class.

        Steps:
            - Instanciate `TempSourceStamp`.
            - update its attributes.
            - check that the `asDict()` method return correct values.

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
