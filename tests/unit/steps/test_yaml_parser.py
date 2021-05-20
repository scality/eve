"""Unit tests of `eve.steps.yaml_parser`."""

from __future__ import absolute_import

import os

from buildbot.plugins import util
from buildbot.process import remotetransfer
from buildbot.process.results import FAILURE, SUCCESS
from buildbot.test.fake.remotecommand import Expect, ExpectRemoteRef
from buildbot.test.util import steps
from buildbot.test.util.misc import TestReactorMixin
from twisted.trial import unittest

from eve.steps import yaml_parser
from tests.util.yaml_factory import RawYaml, SingleCommandYaml


class TestReadConfFromYamlExecution(steps.BuildStepMixin, TestReactorMixin,
                                    unittest.TestCase):
    def setUp(self):
        util.env = util.load_env([
            ('ARTIFACTS_PREFIX', 'prefix'),
            ('ARTIFACTS_PUBLIC_URL', 'foo.bar.baz'),
            ('DOCKER_SCHEDULER_NAME', 'local_scheduler'),
            ('KUBE_POD_SCHEDULER_NAME', 'kube_pod_scheduler'),
            ('FORCE_SCHEDULER_NAME', 'forcescheduler'),
            ('GIT_SLUG', 'git_slug'),
            ('HIDE_INTERNAL_STEPS', '1'),
            ('LOCAL_SCHEDULER_NAME', 'docker_scheduler'),
            ('OPENSTACK_SCHEDULER_NAME', 'openstack_scheduler'),
            ('PATCHER_FILE_PATH', ''),
            ('PROLONG_SCHEDULER_NAME', 'prolongscheduler'),
            ('PROMOTE_SCHEDULER_NAME', 'promotescheduler'),
        ])
        self.setUpTestReactor()
        return self.setUpBuildStep()

    def tearDown(self):
        if os.path.exists(self.step.masterdest):
            os.unlink(self.step.masterdest)
        return self.tearDownBuildStep()

    def setupStep(self, yaml):
        super(TestReadConfFromYamlExecution, self).setupStep(
            yaml_parser.ReadConfFromYaml('main.yml'))

        # mock addStepsAfterCurrentStep
        self.step.build.addStepsAfterCurrentStep = lambda *args, **kw: None

        self.expectCommands(
            Expect('uploadFile', dict(
                workersrc='main.yml', workdir='wkdir',
                blocksize=262144, maxsize=None, keepstamp=False,
                writer=ExpectRemoteRef(remotetransfer.FileWriter)))
            + 0)

        if isinstance(yaml, RawYaml):
            yaml.filedump(self.step.masterdest)
        else:
            with open(self.step.masterdest, 'w') as fp:
                fp.write(yaml)

    def testBasic(self):
        self.setupStep(SingleCommandYaml('exit 0'))
        self.expectOutcome(SUCCESS)
        return self.runStep()

    def testUnsupportedFormatChar(self):
        self.setupStep(SingleCommandYaml('echo "%(prop:revision)j"'))
        self.expectOutcome(FAILURE)
        self.expectLogfile('stderr',
                           'Error in yaml file:\n'
                           '  Unsupported format character "j" line 8: '
                           '"%(prop:revision)j"')
        return self.runStep()

    def testWrongYamlSyntax(self):
        self.setupStep(RawYaml('foo: bar: baz'))
        self.expectOutcome(FAILURE)
        self.expectLogfile('stderr',
                           'Error in yaml file:\n'
                           'mapping values are not allowed here\n'
                           '  in "<unicode string>", line 1, column 9:\n'
                           '    foo: bar: baz\n'
                           '            ^')
        return self.runStep()

    def testWrongYamlType(self):
        self.setupStep(RawYaml('deadbeef'))
        self.expectOutcome(FAILURE)
        self.expectLogfile('stderr',
                           'Error in yaml file:\nShould define a mapping')
        return self.runStep()
