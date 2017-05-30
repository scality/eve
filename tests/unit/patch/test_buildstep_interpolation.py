"""Unit tests of `eve.patch.buildstep_interpolation`.

This module simply test the different components of the
`eve.patch.buildstep_interpolation` module.

Here are the tested components :
    * `patch()` function

"""

from buildbot.process.buildstep import BuildStep
from eve.patch.buildstep_interpolation import patch
from twisted.trial import unittest


class TestBuildStepInterpolation(unittest.TestCase):
    def test_patch(self):
        """Test `patch()` properly monkeypatch `BuildStep` class.

        The `patch()` function should patch the `__init__()` and `startStep()`
        methods from the `BuildStep` class exported by
        `buildbot.process.buildstep` and replace it by decorated
        methods provided in `eve.patch.buildstep_interpolation`.

        """

        init_method = BuildStep.__init__
        startstep_method = BuildStep.startStep
        patch()

        # Since we are each time returning freshly created functions,
        # it is irrelevant to use the '=='. Just make sure that the function
        # pointers aren't the same.
        self.assertNotEqual(BuildStep.__init__, init_method)
        self.assertNotEqual(BuildStep.startStep, startstep_method)
