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
from buildbot.process.properties import Interpolate
from buildbot.process.results import SKIPPED, SUCCESS
from buildbot.test.fake.remotecommand import ExpectShell
from buildbot.test.util import config, steps
from twisted.trial import unittest

from eve.steps.artifacts import (GetArtifactsFromStage,
                                 MalformedArtifactsNameProperty, Upload,
                                 Uploadv3)


class TestUpload(steps.BuildStepMixin, unittest.TestCase,
                 config.ConfigErrorsMixin):
    def setUp(self):
        util.env = util.load_env([
            ('ARTIFACTS_PREFIX', 'prefix-'),
            ('OPENSTACK_BUILDER_NAME', 'openstack'),
        ])
        return self.setUpBuildStep()

    def tearDown(self):
        return self.tearDownBuildStep()

    def setupStep(self, *args, **kwargs):
        res = super(TestUpload, self).setupStep(*args, **kwargs)
        self.properties.setProperty('eve_api_version', '0.2', 'setUp')
        self.properties.setProperty('artifacts_name',
                                    'githost:owner:repo:prefix-'
                                    '0.0.0.0.r190101000000.1234567.'
                                    'pre-merge.12345678', 'setUp')
        self.properties.setProperty('product_version', '0.0.0', 'setUp')
        return res

    def test_bad_artifacts_names(self):
        self.setupStep(Upload(name='Upload',
                              source='/absolute/path'))

        self.properties.setProperty('artifacts_name',
                                    'githost:owner:repo:prefix-bad-name',
                                    'setUp')

        self.expectException(MalformedArtifactsNameProperty)

        return self.runStep()

    def test_arg_interpolate(self):
        self.setupStep(Upload(name='Upload',
                              source=Interpolate('%(kw:foo)s', foo='bar')))
        self.expectCommands(
            ExpectShell(
                workdir='build/bar',
                maxTime=3610,
                command='find -L -type f -print0 | '
                'sed -e "s:\\(^\\|\\x0\\)\\./:\\1:g" | '
                'xargs -0 -n 1 -t -P 16 '
                '-I @ sh -c \'curl --silent --fail --show-error '
                '--max-time 3600 -T "@" '
                '"http://artifacts/upload/githost:owner:repo:prefix-'
                '0.0.0.0.r190101000000.1234567.pre-merge.12345678/"'
                '$(echo "@" | sed -e "s: :%20:g")\''
            )
            + 0)
        self.expectOutcome(result=SUCCESS)
        return self.runStep()

    def test_absolute_source(self):
        self.setupStep(Upload(name='Upload',
                              source='/absolute/path'))
        self.expectCommands(
            ExpectShell(
                workdir='/absolute/path',
                maxTime=3610,
                command='find -L -type f -print0 | '
                'sed -e "s:\\(^\\|\\x0\\)\\./:\\1:g" | '
                'xargs -0 -n 1 -t -P 16 '
                '-I @ sh -c \'curl --silent --fail --show-error '
                '--max-time 3600 -T "@" '
                '"http://artifacts/upload/githost:owner:repo:prefix-'
                '0.0.0.0.r190101000000.1234567.pre-merge.12345678/"'
                '$(echo "@" | sed -e "s: :%20:g")\''
            )
            + 0)
        self.expectOutcome(result=SUCCESS)
        return self.runStep()

    def test_artifacts_upload_on_alpine(self):
        self.setupStep(
            Uploadv3(
                name='Upload',
                source='/absolute/path'
            )
        )
        self.expectCommands(
            ExpectShell(
                workdir='/absolute/path',
                maxTime=3610,
                command='find -L -type f -print0 | '
                'sed -e "s:\\(^\\|\\x0\\)\\./:\\1:g" | '
                'xargs -0 -n 1 -t '
                '-I @ sh -c \'curl --silent --fail --show-error '
                '--max-time 3600 -T "@" '
                '"http://artifacts/upload/githost:owner:repo:prefix-'
                '0.0.0.0.r190101000000.1234567.pre-merge.12345678/"'
                '$(echo "@" | sed -e "s: :%20:g")\''
            )
            + 0
        )
        self.properties.setProperty(
            'distribution_id',
            'alpine',
            'SetWorkerDistro'
        )
        self.expectOutcome(result=SUCCESS)
        return self.runStep()


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
