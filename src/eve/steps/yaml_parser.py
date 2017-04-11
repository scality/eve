import time
import re
from fnmatch import fnmatch
from tempfile import mktemp

import yaml
from buildbot.plugins import steps, util
from buildbot.process.buildstep import BuildStep
from buildbot.process.properties import Interpolate
from buildbot.process.results import CANCELLED, FAILURE, SUCCESS
from buildbot.steps.master import SetProperty
from buildbot.steps.shell import SetPropertyFromCommand
from buildbot.steps.transfer import FileUpload
from packaging import version
from twisted.internet import defer
from twisted.logger import Logger

EVE_FOLDER = 'eve'
EVE_MAIN_YAML = 'main.yml'
EVE_MAIN_YAML_FULL_PATH = '%s/%s' % (EVE_FOLDER, EVE_MAIN_YAML)


class StepPatcher(object):
    """Generic hook to patch step types and parameters."""

    logger = Logger('eve.steps.StepPatcher')

    def __init__(self, config=None):
        config = config or {}
        skip_tests = config.get('skip_tests', [])
        self.skip_regexp = None
        if not skip_tests:
            return
        if isinstance(skip_tests, basestring):
            try:
                self.skip_regexp = re.compile(skip_tests)
            except re.error as err:
                self.logger.error(
                    "Couldn't compile a regexp from '{regexp}': {err}",
                    regexp=skip_tests, err=err
                )
        elif isinstance(skip_tests, (list, tuple)):
            try:
                self.skip_regexp = re.compile('|'.join(skip_tests))
            except (TypeError, re.error) as err:
                self.logger.error(
                    "Couldn't compile a master regexp from '{regexp}': {err}",
                    regexp=skip_tests, err=err
                )

    def patch(self, step_type, params):
        if not self.skip_regexp:
            return step_type, params

        if self.skip_regexp.match(params.get('name', '')):
            params['doStepIf'] = False
            params['descriptionDone'] = 'Temporarily disabled'

        return step_type, params


class ReadConfFromYaml(FileUpload):
    """Load the YAML file to `conf` property.

    This step Reads the YAML file and converts it to a `conf` property which
    is made available to the following steps.
    """
    logger = Logger('eve.steps.ReadConfFromYaml')

    def __init__(self, **kwargs):
        self.masterdest = mktemp()
        FileUpload.__init__(
            self,
            name='read %s' % EVE_MAIN_YAML_FULL_PATH,
            workersrc=EVE_MAIN_YAML_FULL_PATH,
            masterdest=self.masterdest,
            haltOnFailure=True,
            hideStepIf=lambda results, s: results == SUCCESS,
            **kwargs)

    @defer.inlineCallbacks
    def run(self):
        result = yield FileUpload.run(self)
        if result != SUCCESS:
            self.addCompleteLog('stderr', 'Could not find %s' %
                                EVE_MAIN_YAML_FULL_PATH)
            defer.returnValue(result)

        raw_conf = open(self.masterdest).read()
        self.addCompleteLog(EVE_MAIN_YAML_FULL_PATH, raw_conf)
        conf = yaml.load(raw_conf)

        # Extract Eve API version (call str() to support buggy yaml files)
        if conf and 'version' in conf.keys():
            eve_api_version = str(conf['version'])
        else:
            eve_api_version = '0.1'

        # Expand entries with several branch patterns
        try:
            branches = conf['branches']
        except (TypeError, KeyError):
            self.addCompleteLog('stderr', 'Could not find the branches field'
                                          'in %s' % EVE_MAIN_YAML_FULL_PATH)
            defer.returnValue(FAILURE)

        new_branches = {}
        for branch_patterns, branch_conf in branches.items():
            for branch_pattern in branch_patterns.split(','):
                new_branches[branch_pattern.strip()] = branch_conf
        conf['branches'] = new_branches
        self.setProperty('conf', conf, 'ReadConfFromYaml')
        self.setProperty('start_time', str(time.time()))

        # Find the stage name from the branch name
        branch = self.getProperty('branch')
        if branch is None:
            branch = 'default'
        for branch_pattern, branch_conf in conf['branches'].items():
            self.logger.debug('Checking if <{branch}> matches <{pattern}>',
                              branch=branch, pattern=branch_pattern)
            if fnmatch(branch, branch_pattern):
                stage_name = branch_conf['stage']
                self.logger.debug('<{branch}> matched <{branch_pattern}>',
                                  branch=branch, branch_pattern=branch_pattern)
                break
        else:
            self.logger.debug('No branch match. Using default branch config.')
            try:
                stage_name = conf['branches']['default']['stage']
            except KeyError:
                self.addCompleteLog(
                    'stderr', 'Branch <%s> not covered by yaml file' % branch)
                defer.returnValue(CANCELLED)

        self.setProperty('stage_name', stage_name, 'ReadConfFromYaml Step')

        self.build.addStepsAfterCurrentStep([
            SetProperty(
                name='get the API version',
                property='eve_api_version',
                hideStepIf=lambda results, s: results == SUCCESS,
                value=eve_api_version),
            steps.TriggerStages([
                stage_name
            ], waitForFinish=True, haltOnFailure=True)
        ])

        # compute artifact_name property starting from Eve API 0.2
        if version.parse(eve_api_version) >= version.parse('0.2'):
            buildnumber = str(self.getProperty('buildnumber'))
            self.build.addStepsAfterCurrentStep([
                SetPropertyFromCommand(
                    name='get the commit short_revision',
                    command=Interpolate(
                        'git -C %(prop:master_builddir)s/build' +
                        ' rev-parse --verify --short ' +
                        branch
                    ),
                    hideStepIf=lambda results, s: results == SUCCESS,
                    property='commit_short_revision'),
                SetPropertyFromCommand(
                    name='get the commit timestamp',
                    command=Interpolate(
                        'date -u --date=@' +
                        '`git -C %(prop:master_builddir)s/build' +
                        ' show -s --format=%%ct ' + branch +
                        '` +%%y%%m%%d%%H%%M%%S'
                    ),
                    hideStepIf=lambda results, s: results == SUCCESS,
                    property='commit_timestamp'),
                SetProperty(
                    name='get the pipeline name',
                    property='pipeline',
                    hideStepIf=lambda results, s: results == SUCCESS,
                    value=stage_name),
                SetProperty(
                    name='get the b4nb',
                    property='b4nb',
                    hideStepIf=lambda results, s: results == SUCCESS,
                    value=buildnumber.zfill(8)),
            ])

        defer.returnValue(SUCCESS)


class StepExtractor(BuildStep):
    """Extracts and adds the build steps to the current builder.

    This step extracts the build steps from the `conf` property and adds them
    to the current builder. It also adds a step to build an image.
    """
    name = 'step extractor'
    logger = Logger('eve.steps.StepExtractor')

    def run(self):
        conf = self.getProperty('conf')
        step_patcher_config = self.getProperty('step_patcher_config')
        patcher = StepPatcher(step_patcher_config)
        stage_name = self.getProperty('stage_name')
        stage_conf = conf['stages'][stage_name]
        for step in stage_conf['steps']:
            step_type, params = next(step.iteritems())
            step_type, params = patcher.patch(step_type, params)
            bb_step = util.step_factory(globals(), step_type, **params)
            self.build.addStepsAfterLastStep([bb_step])
            self.logger.debug('Add {step} with params : {params}',
                              step=step_type, params=params)
        return defer.succeed(SUCCESS)
