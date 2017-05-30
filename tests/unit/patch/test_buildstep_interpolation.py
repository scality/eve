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
        """Test the patch function in the eve.patch.buildstep_interpolation
        module.

        The patch function should patch the __init__ and startStep
        methods from the BuildStep class exported by the
        buildbot.process.buildstep module and replace it by decorated
        methods provided by the eve.patch.buildstep_interpolation module.
        """

        init_method = BuildStep.__init__
        startstep_method = BuildStep.startStep
        patch()

        # Since we are each time returning freshly created functions,
        # it is irrelevant to use the '=='. Just make sure that the function
        # pointers aren't the same.
        self.assertNotEqual(BuildStep.__init__, init_method)
        self.assertNotEqual(BuildStep.startStep, startstep_method)
