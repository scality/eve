from buildbot.test.util import config as configmixin
from buildbot.test.util import steps as testutil
from eve.steps.artifacts import Upload
from twisted.trial import unittest


class TestUpload(testutil.BuildStepMixin, unittest.TestCase,
                 configmixin.ConfigErrorsMixin):

    def setUp(self):
        return self.setUpBuildStep()

    def tearDown(self):
        return self.tearDownBuildStep()

    def test_constructor_args_validity(self):
        # this checks that an exception is raised for invalid arguments
        self.assertRaisesConfigError(
            "Invalid argument(s) passed to RemoteShellCommand: ",
            lambda: Upload(source='ok', url=[],
                           wrongArg1=1, wrongArg2='two'))

    def test_constructor_args(self):
        upload_step = Upload('tmp', ['link1', 'link2'])
        self.assertEqual(upload_step._retry, (0, 1))
        self.assertEqual(upload_step._source, 'tmp')
        self.assertEqual(upload_step._urls, ['link1', 'link2'])
        self.assertEqual(upload_step.workdir, 'build/tmp')

    def test_retry_arg(self):
        upload_step = Upload('/tmp', ['link1', 'link2'], retry=(1, 2))
        self.assertEqual(upload_step._retry, (1, 2))
