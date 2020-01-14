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

import time
from collections import defaultdict
from fnmatch import fnmatch
from tempfile import mktemp

import yaml
from buildbot.plugins import steps, util
from buildbot.process.buildstep import BuildStep
from buildbot.process.results import FAILURE, SKIPPED, SUCCESS
from buildbot.steps.transfer import FileUpload
from packaging import version
from twisted.internet import defer
from twisted.logger import Logger

from .base import ConfigurableStepMixin
from .property import EveProperty, EvePropertyFromCommand


class ReadConfFromYaml(FileUpload, ConfigurableStepMixin):
    """Load the YAML file to `conf` property.

    This step Reads the YAML file and converts it to a `conf` property which
    is made available to the following steps.

    """

    name = 'ReadConfFromYaml'

    logger = Logger('eve.steps.ReadConfFromYaml')

    def __init__(self, yaml, **kwargs):
        self.yaml = yaml
        self.masterdest = mktemp()
        FileUpload.__init__(
            self,
            workersrc=self.yaml,
            masterdest=self.masterdest,
            haltOnFailure=True,
            hideStepIf=util.hideStepIfSuccess,
            **kwargs)

    @defer.inlineCallbacks
    def run(self):
        result = yield FileUpload.run(self)
        if result != SUCCESS:
            self.addCompleteLog('stderr', 'Could not find %s' % self.yaml)
            defer.returnValue(result)

        self.setProperty('conf_path', self.masterdest,
                         'ReadConfFromYaml')
        raw_conf = open(self.masterdest).read()
        self.addCompleteLog(self.yaml, raw_conf)

        # Make sure all interpolation have correct syntax
        d = defaultdict(str)
        try:
            raw_conf % d
        except ValueError as error:
            if 'unsupported format character' in error.args[0]:
                msg = error.args[0]
                index = int(msg[msg.find('index') + 6:])
                fmt = raw_conf[:index + 1]
                line = fmt.count('\n') + 1
                fmt = fmt[fmt.rfind('%'):]
                self.addCompleteLog('stderr',
                                    'Error in yaml file:\n  '
                                    'Unsupported format character "%s" line '
                                    '%d: "%s"' % (fmt[-1], line, fmt))
                defer.returnValue(FAILURE)
            else:
                raise
        except TypeError:
            pass

        # Make sure yaml is properly formatted
        try:
            conf = self.getEveConfig()
        except yaml.YAMLError as error:
            self.addCompleteLog('stderr', 'Error in yaml file:\n%s' % error)
            defer.returnValue(FAILURE)

        # Yaml should define a mapping
        if not isinstance(conf, dict):
            self.addCompleteLog('stderr',
                                'Error in yaml file:\nShould define a mapping')
            defer.returnValue(FAILURE)

        # Extract Eve API version (call str() to support buggy yaml files)
        if 'version' in conf.keys():
            eve_api_version = str(conf['version'])
        else:
            eve_api_version = '0.1'

        # Expand entries with several branch patterns
        try:
            branches = conf['branches']
        except (TypeError, KeyError):
            self.addCompleteLog('stderr', 'Could not find the branches field'
                                          'in %s' % self.yaml)
            defer.returnValue(FAILURE)

        new_branches = {}
        for branch_patterns, branch_conf in branches.items():
            for branch_pattern in branch_patterns.split(','):
                new_branches[branch_pattern.strip()] = branch_conf
        conf['branches'] = new_branches
        self.setProperty('start_time', str(time.time()))

        # Use the given stage if any (forced build)
        stage_name = self.getProperty('force_stage')
        branch = self.getProperty('branch')
        if branch is None:
            branch = 'default'
        if stage_name:
            self.logger.debug('Stage forced by user to <{stage}',
                              stage=stage_name)
        else:
            # Else find the stage name from the branch name
            for branch_pattern, branch_conf in conf['branches'].items():
                self.logger.debug('Checking if <{branch}> matches <{pattern}>',
                                  branch=branch, pattern=branch_pattern)
                if fnmatch(branch, branch_pattern):
                    stage_name = branch_conf['stage']
                    self.logger.debug('<{branch}> matched <{branch_pattern}>',
                                      branch=branch,
                                      branch_pattern=branch_pattern)
                    break
            else:
                self.logger.debug('No branch match. '
                                  'Using default branch config.')
                try:
                    stage_name = conf['branches']['default']['stage']
                except KeyError:
                    self.addCompleteLog(
                        'stderr',
                        'Branch <%s> not covered by yaml file' % branch)
                    self.build.results = SKIPPED
                    defer.returnValue(SKIPPED)

        if 'bootstrap' in conf.get('stages', {}):
            self.addCompleteLog('stderr',
                                'Error in yaml file:\n'
                                'boostrap is reserved and '
                                'cannot be used as a stage name')
            defer.returnValue(FAILURE)

        if stage_name not in conf.get('stages', {}):
            self.addCompleteLog('stderr',
                                'Error in yaml file:\n'
                                'the specified stage cannot be '
                                'found (%s)' % stage_name)
            defer.returnValue(FAILURE)

        self.build.addStepsAfterCurrentStep([
            GetApiVersion(eve_api_version=eve_api_version),
            steps.TriggerStages([
                stage_name
            ], waitForFinish=True, haltOnFailure=True)
        ])

        # compute artifact_name property starting from Eve API 0.2
        if version.parse(eve_api_version) >= version.parse('0.2'):
            buildnumber = str(self.getProperty('buildnumber'))
            self.build.addStepsAfterCurrentStep([
                GetCommitShortVersion(branch=branch),
                GetCommitTimestamp(),
                steps.SetArtifactsName(
                    buildnumber=buildnumber,
                    stage_name=stage_name),
                steps.SetArtifactsPublicURL(),
            ])

        # Read patcher conf and populate related properties
        scheduler = self.getProperty('scheduler')
        if scheduler not in (util.env.FORCE_SCHEDULER_NAME,
                             util.env.PROMOTE_SCHEDULER_NAME):
            self.build.addStepsAfterCurrentStep([
                steps.PatcherConfig(
                    conf_path=util.env.PATCHER_FILE_PATH,
                    stage=stage_name,
                    name='collect system-level skips for this build',
                    doStepIf=bool(util.env.PATCHER_FILE_PATH),
                    hideStepIf=util.hideStepIfSuccessOrSkipped)])

        defer.returnValue(SUCCESS)


class StepExtractor(BuildStep, ConfigurableStepMixin):
    """Extract and add the build steps to the current builder.

    This step extracts the build steps from the `conf` property and adds them
    to the current builder. It also adds a step to build an image.

    """

    name = 'step extractor'
    logger = Logger('eve.steps.StepExtractor')

    def run(self):
        conf = self.getEveConfig()
        patcher_config = self.getProperty('patcher_config')
        patcher = util.Patcher(patcher_config)

        stage_name = self.getProperty('stage_name')
        stage_conf = conf['stages'][stage_name]
        for step in reversed(stage_conf['steps']):
            step_type, params = next(iter(step.items()))
            step_type, params = patcher.patch_step(step_type, params)
            bb_step = util.step_factory(globals(), step_type, **params)
            self.build.addStepsAfterCurrentStep([bb_step])
            self.logger.debug('Add {step} with params: {params}',
                              step=step_type, params=params)
        return SUCCESS


class GetCommitShortVersion(EvePropertyFromCommand):
    def __init__(self, branch):
        super(GetCommitShortVersion, self).__init__(
            name='get the commit short_revision',
            command=[
                'git',
                'rev-parse',
                '--verify',
                '--short',
                branch,
            ],
            hideStepIf=util.hideStepIfSuccess,
            property='commit_short_revision',
            haltOnFailure=True,
            logEnviron=False)


class GetCommitTimestamp(EvePropertyFromCommand):
    def __init__(self):
        super(GetCommitTimestamp, self).__init__(
            name='get the commit timestamp',
            command=[
                'git',
                'log',
                '-1',
                '--format=%cd',
                '--date=format-local:%y%m%d%H%M%S',
            ],
            hideStepIf=util.hideStepIfSuccess,
            haltOnFailure=True,
            property='commit_timestamp',
            logEnviron=False)


class GetApiVersion(EveProperty):
    def __init__(self, eve_api_version):
        super(GetApiVersion, self).__init__(
            name='get the API version',
            property='eve_api_version',
            hideStepIf=util.hideStepIfSuccess,
            value=eve_api_version)
