import re
import time
from fnmatch import fnmatch
from tempfile import mktemp

import netifaces
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


class ReadConfFromYaml(FileUpload):
    """Load the YAML file to `conf` property.

    This step Reads the YAML file and converts it to a `conf` property which
    is made available to the following steps.
    """
    logger = Logger('eve.steps.ReadConfFromYaml')

    def __init__(self, **kwargs):
        self.yaml = util.env.PROJECT_YAML
        self.masterdest = mktemp()
        FileUpload.__init__(
            self,
            name='read %s' % self.yaml,
            workersrc=self.yaml,
            masterdest=self.masterdest,
            haltOnFailure=True,
            hideStepIf=lambda results, s: results == SUCCESS,
            **kwargs)

    @defer.inlineCallbacks
    def run(self):
        result = yield FileUpload.run(self)
        if result != SUCCESS:
            self.addCompleteLog('stderr', 'Could not find %s' %
                                self.yaml)
            defer.returnValue(result)

        raw_conf = open(self.masterdest).read()
        self.addCompleteLog(self.yaml, raw_conf)
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
                                          'in %s' % self.yaml)
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
            GetApiVersion(eve_api_version=eve_api_version),
            steps.TriggerStages([
                stage_name
            ], waitForFinish=True, haltOnFailure=True)
        ])

        docker_host_ip = get_docker_host_ip()

        # compute artifact_name property starting from Eve API 0.2
        if version.parse(eve_api_version) >= version.parse('0.2'):
            buildnumber = str(self.getProperty('buildnumber'))
            self.build.addStepsAfterCurrentStep([
                GetCommitShortVersion(branch=branch),
                GetCommitTimestamp(),
                GetPipelineName(stage_name=stage_name),
                GetB4NB(buildnumber=buildnumber),
                SetArtifactsBaseName(),
                SetArtifactsName(),
                SetArtifactsLocalReverseProxy(docker_host_ip=docker_host_ip),
                SetArtifactsPrivateURL(docker_host_ip=docker_host_ip),
                SetArtifactsPublicURL(),
            ])

        defer.returnValue(SUCCESS)


class StepPatcher(object):
    """Generic hook to patch step types and parameters."""

    logger = Logger('eve.steps.StepPatcher')

    def __init__(self, config=None):
        config = config or {}
        self.logger.info("Running with conf {conf}", conf=config)
        skip_tests = config.get('skip_steps', [])
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

        name = params.get('name', '')
        self.logger.info("name: {name} regexp: {regexp}", name=name,
                         regexp=self.skip_regexp)
        if name and self.skip_regexp.match(name):
            params['doStepIf'] = False
            params['descriptionDone'] = 'Temporarily disabled'

        return step_type, params


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


class GetCommitShortVersion(SetPropertyFromCommand):
    def __init__(self, branch):
        super(GetCommitShortVersion, self).__init__(
            name='get the commit short_revision',
            command=Interpolate(
                'git rev-parse --verify --short ' + branch),
            hideStepIf=lambda results, s: results == SUCCESS,
            property='commit_short_revision',
            haltOnFailure=True)


class GetCommitTimestamp(SetPropertyFromCommand):
    def __init__(self):
        super(GetCommitTimestamp, self).__init__(
            name='get the commit timestamp',
            command='git log -1 --format=%cd '
                    '--date="format-local:%y%m%d%H%M%S"',
            hideStepIf=lambda results, s: results == SUCCESS,
            haltOnFailure=True,
            property='commit_timestamp')


class GetPipelineName(SetProperty):
    def __init__(self, stage_name):
        super(GetPipelineName, self).__init__(
            name='get the pipeline name',
            property='pipeline',
            hideStepIf=lambda results, s: results == SUCCESS,
            haltOnFailure=True,
            value=stage_name)


class GetB4NB(SetProperty):
    def __init__(self, buildnumber):
        super(GetB4NB, self).__init__(
            name='get the b4nb',
            property='b4nb',
            hideStepIf=lambda results, s: results == SUCCESS,
            haltOnFailure=True,
            value=buildnumber.zfill(8))


class SetArtifactsBaseName(SetPropertyFromCommand):
    def __init__(self):
        super(SetArtifactsBaseName, self).__init__(
            name='set the artifacts base name',
            command=Interpolate('echo %(prop:git_host)s'
                                ':%(prop:git_owner)s:' +
                                util.env.GIT_SLUG +
                                ':%(prop:artifacts_prefix)s'
                                '%(prop:product_version)s'
                                '.r%(prop:commit_timestamp)s'
                                '.%(prop:commit_short_revision)s'),
            hideStepIf=lambda results, s: results == SUCCESS,
            property='artifacts_base_name')


class SetArtifactsName(SetPropertyFromCommand):
    def __init__(self):
        super(SetArtifactsName, self).__init__(
            name='set the artifacts name',
            command=Interpolate('echo %(prop:artifacts_base_name)s'
                                '.%(prop:pipeline)s'
                                '.%(prop:b4nb)s'),
            hideStepIf=lambda results, s: results == SUCCESS,
            property='artifacts_name')


class SetArtifactsLocalReverseProxy(SetProperty):
    def __init__(self, docker_host_ip):
        super(SetArtifactsLocalReverseProxy, self).__init__(
            name='set the artifacts local reverse proxy',
            property='artifacts_local_reverse_proxy',
            hideStepIf=lambda results, s: results == SUCCESS,
            value='http://' + docker_host_ip + ':1080/')


class SetArtifactsPrivateURL(SetPropertyFromCommand):
    def __init__(self, docker_host_ip):
        super(SetArtifactsPrivateURL, self).__init__(
            name='set the artifacts private url',
            command=Interpolate('echo http://' + docker_host_ip +
                                ':1080/builds/'
                                '%(prop:artifacts_name)s'),
            hideStepIf=lambda results, s: results == SUCCESS,
            property='artifacts_private_url')


class SetArtifactsPublicURL(SetPropertyFromCommand):
    def __init__(self):
        super(SetArtifactsPublicURL, self).__init__(
            name='set the artifacts public url',
            command=Interpolate('echo ' + util.env.ARTIFACTS_URL +
                                '/%(prop:artifacts_name)s'),
            hideStepIf=lambda results, s: results == SUCCESS,
            property='artifacts_public_url')


class GetApiVersion(SetProperty):
    def __init__(self, eve_api_version):
        super(GetApiVersion, self).__init__(
            name='get the API version',
            property='eve_api_version',
            hideStepIf=lambda results, s: results == SUCCESS,
            value=eve_api_version)


def get_docker_host_ip():
    docker_host_ip = '127.0.0.1'  # Dummy default value
    try:
        docker_addresses = netifaces.ifaddresses('docker0')
    except ValueError:
        pass
    else:
        try:
            docker_host_ip = (docker_addresses[netifaces.AF_INET][0]['addr'])
        except KeyError:
            pass
    return docker_host_ip
