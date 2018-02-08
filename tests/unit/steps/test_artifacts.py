# Copyright 2017 Scality
#
# This file is part of Eve.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.
"""Unit tests of `eve.steps.artifacts`."""

from __future__ import absolute_import

from buildbot.plugins import util
from buildbot.process.results import SKIPPED, SUCCESS
from buildbot.test.fake.remotecommand import ExpectShell
from buildbot.test.util import config, steps
from twisted.trial import unittest

from eve.steps.artifacts import GetArtifactsFromStage, Upload


class TestUpload(steps.BuildStepMixin, unittest.TestCase,
                 config.ConfigErrorsMixin):
    def setUp(self):
        return self.setUpBuildStep()

    def tearDown(self):
        return self.tearDownBuildStep()

    def test_init_args_validity(self):
        """Test that an exception is raised for invalid argument."""
        self.assertRaisesConfigError(
            "Invalid argument(s) passed to RemoteShellCommand: ",
            lambda: Upload(source='ok', url=[], wrongArg1=1, wrongArg2='two'))

    def test_init_args(self):
        """Test that the constructor args are stored in the class."""
        upload_step = Upload('tmp', ['link1', 'link2'])
        self.assertEqual(upload_step._retry, (0, 1))
        self.assertEqual(upload_step._source, 'tmp')
        self.assertEqual(upload_step._urls, ['link1', 'link2'])
        self.assertEqual(upload_step.workdir, 'build/tmp')

    def test_retry_arg(self):
        """Test that the retry constructor arg is stored in the class."""
        upload_step = Upload('/tmp', ['link1', 'link2'], retry=(1, 2))
        self.assertEqual(upload_step._retry, (1, 2))


class TestGetArtifactsFromStage(steps.BuildStepMixin, unittest.TestCase):
    def setUp(self):
        util.env = util.load_env([
            ('ARTIFACTS_PREFIX', 'prefix'),
        ])
        return self.setUpBuildStep()

    def tearDown(self):
        return self.tearDownBuildStep()

    def setupStep(self, stage='pre-merge', property='artifacts',
                  expect_command=True, stdout='Location: http://a/builds/foo'):
        super(TestGetArtifactsFromStage, self).setupStep(
            GetArtifactsFromStage(stage,
                                  property=property,
                                  name='GetArtifactsFromStage'))
        if expect_command:
            self.expectCommands(
                ExpectShell(workdir='wkdir',
                            command=[
                                'curl',
                                '-L',
                                '--fail',
                                '-I',
                                'http://artifacts/last_success/:::%s.r..%s' % (
                                    util.env.ARTIFACTS_PREFIX, stage)
                            ])
                + ExpectShell.log('stdio', stdout=stdout)
                + 0)

    def testBasic(self):
        self.setupStep()
        self.expectOutcome(SUCCESS)
        self.expectProperty('artifacts', 'foo', 'GetArtifactsFromStage')
        return self.runStep()

    def testSkipSetProperty(self):
        self.setupStep(expect_command=False)
        self.properties.setProperty('artifacts', 'spam', 'Force Build Form')
        self.expectOutcome(SKIPPED)
        self.expectProperty('artifacts', 'spam', 'Force Build Form')
        return self.runStep()

    def testOverrideProperty(self):
        self.setupStep()
        self.properties.setProperty('artifacts', 'spam', 'someone')
        self.expectOutcome(SUCCESS)
        self.expectProperty('artifacts', 'foo', 'GetArtifactsFromStage')
        return self.runStep()
