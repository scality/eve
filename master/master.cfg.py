# coding: utf-8
import json
import shutil
from fnmatch import fnmatch
from os import environ, getcwd, path
from random import randint

import docker
import yaml
from buildbot.changes.gitpoller import GitPoller
from buildbot.config import BuilderConfig
from buildbot.plugins import steps
from buildbot.process.buildstep import BuildStep
from buildbot.process.factory import BuildFactory
from buildbot.process.properties import Interpolate, Property
from buildbot.process.results import FAILURE, SUCCESS, WARNINGS, Results
from buildbot.reporters.http import HttpStatusPushBase
from buildbot.scheduler import AnyBranchScheduler
from buildbot.schedulers.forcesched import ForceScheduler
from buildbot.schedulers.triggerable import Triggerable
from buildbot.steps.http import HTTPStep
from buildbot.steps.shell import SetPropertyFromCommand, ShellCommand
from buildbot.steps.source.base import Source
from buildbot.steps.source.git import Git
from buildbot.steps.trigger import Trigger
from buildbot.worker.docker import DockerLatentWorker
from buildbot.worker.local import LocalWorker
from buildbot.www.oauth2 import GoogleAuth
from buildbot.www.authz import Authz, endpointmatchers, roles
from requests.auth import HTTPBasicAuth
from twisted.internet.defer import inlineCallbacks, returnValue, succeed
from twisted.logger import Logger
from twisted.python.reflect import namedModule

##########################
# Constants
##########################
LOCAL_WORKER_NAME = 'lw-001'
BOOTSTRAP_BUILDER_NAME = 'bootstrap'
BOOTSTRAP_SCHEDULER_NAME = 's-bootstrap'
TRIGGERABLE_BUILDER_NAME = 'triggerable'
TRIGGERABLE_SCHEDULER_NAME = 's-triggerable'
MAX_DOCKER_WORKERS = 10
EVE_FOLDER = 'eve'
EVE_MAIN_YAML = 'main.yml'
EVE_MAIN_YAML_FULL_PATH = '%s/%s' % (EVE_FOLDER, EVE_MAIN_YAML)

##########################
# Set/Check environment variables
##########################
# git
GIT_REPO = environ['GIT_REPO']
assert GIT_REPO
GIT_KEY_PATH = environ['GIT_KEY_PATH']
assert path.isfile(GIT_KEY_PATH), 'Did not find git RSA cert in %s' %\
                                  GIT_KEY_PATH

# docker
assert '//' in environ['DOCKER_HOST']
DOCKER_HOST = environ['DOCKER_HOST']
EXTERNAL_URL = environ['EXTERNAL_URL']
assert EXTERNAL_URL
MASTER_DOCKER_NAME = environ['MASTER_DOCKER_NAME']
assert MASTER_DOCKER_NAME
MASTER_ADDRESS = MASTER_DOCKER_NAME

DOCKER_CERT_PATH = None
if path.isdir(environ['DOCKER_CERT_PATH']):
    DOCKER_CERT_PATH = environ['DOCKER_CERT_PATH']
    DOCKER_CERT_PATH_CA = path.join(DOCKER_CERT_PATH, 'ca.pem')
    DOCKER_CERT_PATH_KEY = path.join(DOCKER_CERT_PATH, 'key.pem')
    DOCKER_CERT_PATH_CERT = path.join(DOCKER_CERT_PATH, 'cert.pem')
    assert path.isfile(DOCKER_CERT_PATH_CA), DOCKER_CERT_PATH_CA
    assert path.isfile(DOCKER_CERT_PATH_KEY), DOCKER_CERT_PATH_KEY
    assert path.isfile(DOCKER_CERT_PATH_CERT), DOCKER_CERT_PATH_CERT

if DOCKER_CERT_PATH:
    TLS_CONFIG = docker.tls.TLSConfig(
        client_cert=(
            DOCKER_CERT_PATH_CERT,
            DOCKER_CERT_PATH_KEY),
        ca_cert=DOCKER_CERT_PATH_CA,
        verify=False)
else:
    TLS_CONFIG = None

# bitbucket
EVE_BITBUCKET_LOGIN = environ['EVE_BITBUCKET_LOGIN']
EVE_BITBUCKET_PWD = environ['EVE_BITBUCKET_PWD']

OAUTH2_CLIENT_ID = environ['OAUTH2_CLIENT_ID']
OAUTH2_CLIENT_SECRET = environ['OAUTH2_CLIENT_SECRET']

PROJECT_NAME = environ['PROJECT_NAME']
PROJECT_URL = environ['PROJECT_URL']

# database
DB_URL = environ['DB_URL']

docker_client = docker.Client(
    base_url=DOCKER_HOST,
    tls=TLS_CONFIG
)

##########################
# Project Identity
##########################
EVE_CONF = BuildmasterConfig = {}
EVE_CONF['title'] = "Eve: pipeline of the %s project" % PROJECT_NAME
EVE_CONF['titleURL'] = PROJECT_URL
EVE_CONF['buildbotURL'] = EXTERNAL_URL

# 'protocols' contains information about protocols which master will use for
# communicating with workers. You must define at least 'port' option that
# workers could connect to your master with this protocol.
# 'port' must match the value configured into the buildworkers (with their
# --master option)
EVE_CONF['protocols'] = {'pb': {'port': 9000}}


##########################
# Web UI
##########################
# Create a basic auth website with the waterfall view and the console view
EVE_CONF['www'] = dict(port=8000,
                       auth=GoogleAuth(OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET),
                       plugins=dict(
                           waterfall_view={},
                           console_view={}))

# Limit write operations to the OAUTH2_CLIENT_ID account except for tests


class DeveloperRoleIfConnected(roles.RolesFromBase):
    """ Sets the 'developer' role to all authenticated users"""

    def getRolesFromUser(self, userDetails):
        if 'email' in userDetails:# and userDetails['email']:
            return ['developer']
        return []

if OAUTH2_CLIENT_ID != 'test':
    authz = Authz(
        allowRules=[
            endpointmatchers.AnyEndpointMatcher(role='developer'),
        ],
        roleMatchers=[
            DeveloperRoleIfConnected()
        ]
    )
    EVE_CONF['www']['authz'] = authz

# DB URL
EVE_CONF['db'] = {
    'db_url': DB_URL,
}


# #########################
# Reporters
# #########################
# Reporters send the build status when finished

class BitbucketBuildStatusPush(HttpStatusPushBase):
    """Send build result to bitbucket build status API."""
    name = "BitbucketBuildStatusPush"
    logger = Logger('eve.steps.BitbucketBuildStatusPush')

    @staticmethod
    def forge_url(build):
        """Forge the BB API URL on which the build status will be posted."""
        sha1 = build['buildset']['sourcestamps'][0]['revision']
        repository = build['properties']['repository'][0]
        owner, repo = repository.split(':')[1].split('/', 1)
        return 'https://api.bitbucket.org/2.0/repositories/' \
               '%(repo_owner)s/%(repo_name)s/commit/%(sha1)s/statuses/build' \
               % {
                   'repo_owner': owner,
                   'repo_name': repo,
                   'sha1': sha1
               }

    @staticmethod
    def forge_messages(stage_name, build):
        """Forge the BB messages that will be displayed on the BB site."""
        message = '%s build#%d ' % (stage_name, build['buildid'])
        if build['complete']:
            results = build['results']
            if results in (SUCCESS, WARNINGS):
                bitbucket_state = 'SUCCESSFUL'
            else:
                bitbucket_state = 'FAILED'
            message += Results[results]
            delay = (build['complete_at'] -
                     build['started_at']).total_seconds()
            message += ' in %d seconds' % delay

        else:
            # This code is never reached. Buildbot does not call a reporter
            # To announce the start of a build
            bitbucket_state = 'INPROGRESS'
            message += ' is in progress...'
        description = ''  # XXX: If we have more infos, here is the place
        return bitbucket_state, message, description

    @inlineCallbacks
    def send(self, build):
        """Send build status to Bitbucket."""

        self.logger.debug('Sending build status to Bitbucket: {buildstatus}',
                          buildstatus=build)

        stage_name = build['properties']['stage_name'][0]
        state, message, description = self.forge_messages(stage_name, build)
        data = {
            'state': state,
            'key': stage_name,
            "name": message,
            "url": build['url'],
            "description": description
        }
        auth = HTTPBasicAuth(EVE_BITBUCKET_LOGIN, EVE_BITBUCKET_PWD)
        response = yield self.session.post(
            self.forge_url(build), data, auth=auth)
        if response.status_code != 201:
            self.logger.error("{response.status_code}: unable to send status "
                              "to bitbucket:\n{response.content}",
                              response=response)

# The status push works only on the main builder (bootstrap)
statpsh = BitbucketBuildStatusPush(builders=['bootstrap'], wantProperties=True)
EVE_CONF['services'] = [statpsh]

##########################
# Workers
##########################
# Create One Local Worker that will bootstrap all the jobs
EVE_CONF['workers'] = [LocalWorker(LOCAL_WORKER_NAME)]

# Then create MAX_DOCKER_WORKERS Docker Workers that will do the real job

DOCKER_WORKERS = []
for i in range(MAX_DOCKER_WORKERS):
    DOCKER_WORKERS.append(
        DockerLatentWorker(
            name='dw%03d-%s' % (i, MASTER_DOCKER_NAME),
            password='pwd%d' % i,  # fixme: stronger passwords
            docker_host=DOCKER_HOST,
            hostconfig={'links': [(MASTER_DOCKER_NAME, MASTER_DOCKER_NAME)]},
            tls=TLS_CONFIG,
            image=Property('docker_image'),
            networking_config=None,
            followStartupLogs=True,
            masterFQDN=MASTER_DOCKER_NAME))
EVE_CONF['workers'].extend(DOCKER_WORKERS)

##########################
# Change Sources
##########################
# the 'change_source' setting tells the buildmaster how it should find out
# about source code changes.

EVE_CONF['change_source'] = []
EVE_CONF['change_source'].append(GitPoller(
    GIT_REPO,
    workdir='gitpoller-workdir',
    branches=True,
    pollinterval=10,
    pollAtLaunch=True,
    buildPushesWithNoCommits=True,
))


##########################
# Custom Build Steps
##########################
class ReadConfFromYaml(SetPropertyFromCommand):
    """Load the YAML file to `conf` property.

    This step Reads the YAML file and converts it to a `conf` property which
    is made available to the following steps.
    """
    logger = Logger('eve.steps.ReadConfFromYaml')

    def __init__(self, **kwargs):
        SetPropertyFromCommand.__init__(
            self,
            name='Read config from %s' % EVE_MAIN_YAML_FULL_PATH,
            command='cat %s' % EVE_MAIN_YAML_FULL_PATH,
            property='conf',
            haltOnFailure=True,
            **kwargs)

    def commandComplete(self, cmd):  # NOQA flake8 to ignore camelCase
        if cmd.didFail():
            return
        conf = yaml.load(self.observer.getStdout())
        self.setProperty(self.property, conf, "ReadConfFromYaml Step")
        self.property_changes[self.property] = conf

        # Find the stage name from the branch name
        branch = self.getProperty('branch', 'default')
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
                self.logger.debug('No default. Stopping here.')
                return
        self.setProperty('stage_name', stage_name, 'ReadConfFromYaml Step')
        self.property_changes['stage_name'] = stage_name
        self.build.addStepsAfterCurrentStep([TriggerStages([stage_name])])


class StepExtractor(BuildStep):
    """Extracts and adds the build steps to the current builder.

    This step extracts the build steps from the `conf` property and adds them
    to the current builder. It also adds a step to build an image.
    """
    name = 'step extractor'
    logger = Logger('eve.steps.StepExtractor')

    def run(self):
        conf = self.getProperty('conf')
        stage_name = self.getProperty('stage_name')
        stage_conf = conf['stages'][stage_name]
        for step in stage_conf['steps']:
            step_type, params = dict.popitem(step)
            try:
                # try to see if the required step is imported or
                # defined in the current context
                _cls = globals()[step_type]
            except KeyError:
                # otherwise import the step from standars buildbot steps
                try:
                    _cls = getattr(steps, step_type)
                except AttributeError:
                    raise Exception('Could not load step %s' % step_type)

            # Replace the %(prop:*)s in the text with an Interpolate obj
            params = replace_with_interpolate(params)

            # hack to prevent displaying passwords stored in env variables
            # on the web interface
            if issubclass(_cls, (ShellCommand, Source)):
                params['logEnviron'] = False

            # hack to avoid putting clear passwords into the YAML file
            # for the HTTP step
            if issubclass(_cls, HTTPStep):
                pwd = params['auth'][1].replace('$', '')
                if pwd in environ:
                    params['auth'] = HTTPBasicAuth(
                        params['auth'][0], environ[pwd])

            # Hack! Buildbot does not accept unicode step names
            if 'name' in params and isinstance(params['name'], unicode):
                params['name'] = params['name'].encode('utf-8')

            step = _cls(**params)
            self.build.addStepsAfterLastStep([step])
            self.logger.debug('Add {step} with params : {params}',
                              step=step_type, params=params)
        return succeed(SUCCESS)


class BuildDockerImage(BuildStep):
    logger = Logger('eve.steps.BuildDockerImage')

    def __init__(self, path, image_name, **kwargs):
        BuildStep.__init__(self, **kwargs)
        self.full_path = path
        self.image_name = image_name
        self.haltOnFailure = True

    @inlineCallbacks
    def run(self):
        # Capture the output of the docker build command in a log object
        stdio = yield self.addLog('stdio')
        stdio.addHeader(
            'Building docker image <%s> fom %s on docker host %s\n' %
            (self.image_name, self.full_path, DOCKER_HOST))
        fail = False
        # assert the directory containing the dockerfile exists
        assert path.exists(self.full_path), \
            '%s does not exist in %s' % (self.full_path, getcwd())
        shutil.copy(GIT_KEY_PATH, self.full_path)
        self.setProperty('docker_image', self.image_name)
        for output in docker_client.build(
                path=self.full_path,
                tag=self.image_name):
            for json_line in output.rstrip().split('\r\n'):
                formatted = json.loads(json_line)
                if 'error' in formatted:
                    stdio.addStderr(formatted['error'] + '\n')
                    raise Exception("ERROR: " + formatted['error'])
                elif 'stream' in formatted:
                    for line in formatted['stream'].split('\n'):
                        if line:
                            stdio.addStdout(formatted['stream'])
                            # self.logger.info(line)
                else:
                    self.logger.info(formatted)
        stdio.finish()
        if fail:
            returnValue(FAILURE)
        returnValue(SUCCESS)


class TriggerStages(BuildStep):

    def __init__(self, stage_names, **kwargs):
        self.stage_names = stage_names
        BuildStep.__init__(self)
        self.kwargs = kwargs
        if 'waitForFinish' not in kwargs:
            kwargs['waitForFinish'] = True

        self.name = 'trigger stage(s) %s' % ','.join(stage_names)

    def run(self):
        conf = self.getProperty('conf')
        stages = []

        build_image_steps = []

        for stage_name in reversed(self.stage_names):
            try:
                docker_path = conf['stages'][stage_name]['image']['path']
            except KeyError:
                return succeed(FAILURE)
            full_docker_path = 'workers/%s/%s/build/%s' % (
                LOCAL_WORKER_NAME,
                BOOTSTRAP_BUILDER_NAME,
                docker_path)
            image_name = '%s-%06d' % (docker_path, randint(0, 999999))
            step = BuildDockerImage(
                name=str('build docker image from %s' % docker_path),
                image_name=image_name,
                path=full_docker_path)
            build_image_steps.append(step)
            stages.append((stage_name, image_name))

        step = TriggerStagesOld(
            stage_names=stages, **self.kwargs)
        self.build.addStepsAfterCurrentStep([step])
        self.build.addStepsAfterCurrentStep(build_image_steps)

        return succeed(SUCCESS)


class TriggerStagesOld(Trigger):
    """Allows to give specific parameter to every scheduler.

    This is a step that allows to start with the properties specified in the
    schedulerNames argument (tuple) instead of using the properties given in
    the set_properties/copy_properties parameters.
    """

    def __init__(self, stage_names, **kwargs):
        Trigger.__init__(self, schedulerNames=stage_names, **kwargs)

    def getSchedulersAndProperties(self):   # NOQA flake8 to ignore camelCase
        conf = self.getProperty('conf')
        return [
            (TRIGGERABLE_SCHEDULER_NAME, {
                'stage_name': stage_name,
                'docker_image': docker_image,
                'conf': conf
            }) for stage_name, docker_image in self.schedulerNames]


# #########################
# Bootstrap Sequence: Schedulers
# #########################
EVE_CONF['schedulers'] = []
EVE_CONF['schedulers'].append(AnyBranchScheduler(
    name=BOOTSTRAP_SCHEDULER_NAME,
    treeStableTimer=None,
    builderNames=[BOOTSTRAP_BUILDER_NAME]))

EVE_CONF['schedulers'].append(ForceScheduler(
    name="force-bootstrap",
    builderNames=[BOOTSTRAP_BUILDER_NAME]))

# #########################
# Bootstrap Sequence: Build step factory
# #########################
bootstrap_factory = BuildFactory()
# Check out the source
bootstrap_factory.addStep(Git(
    repourl=GIT_REPO,
    mode='incremental'))
# Read conf from yaml file
bootstrap_factory.addStep(ReadConfFromYaml())

# #########################
# Bootstrap Sequence: Builders
# #########################
EVE_CONF['builders'] = []
EVE_CONF['builders'].append(
    BuilderConfig(
        name=BOOTSTRAP_BUILDER_NAME,
        workernames=[LOCAL_WORKER_NAME],
        factory=bootstrap_factory))

# #########################
# Triggerable Sequence: Schedulers
# #########################
EVE_CONF['schedulers'].append(Triggerable(
    name=TRIGGERABLE_SCHEDULER_NAME,
    builderNames=[TRIGGERABLE_BUILDER_NAME]))

# #########################
# Triggerable Sequence: Build step factory
# #########################
triggered_factory = BuildFactory()
# Extract steps from conf
triggered_factory.addStep(StepExtractor())

# #########################
# Triggerable Sequence: Builders
# #########################
EVE_CONF['builders'].append(
    BuilderConfig(
        name=TRIGGERABLE_BUILDER_NAME,
        workernames=[dw.name for dw in DOCKER_WORKERS],
        factory=triggered_factory
    ))

# #########################
# Hacks/Bugfixes
# #########################
# Hack to fix Failure: exceptions.TypeError:
# unbound method _defaultCollapseRequestFn()
# must be called with Builder instance as first
# argument (got BuildMaster instance instead)
EVE_CONF['collapseRequests'] = False

# Hack to fix a bug stating that LocalWorkers do not have a valid path_module
for w in EVE_CONF['workers']:
    w.path_module = namedModule("posixpath")


# #########################
# Utils
# #########################
def replace_with_interpolate(obj):
    """Interpolate nested %(prop:obj)s in step arguments.

    Read step arguments from the yaml file and replaces them with
    interpolate objects when relevant so they can be replaced with
    properties when run.
    """

    if isinstance(obj, dict):
        return {k: replace_with_interpolate(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_with_interpolate(elem) for elem in obj]
    elif isinstance(obj, str) and 'prop:' in obj:
        return Interpolate(obj)
    else:
        return obj
