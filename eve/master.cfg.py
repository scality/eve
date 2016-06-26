import os
import shutil
from os import environ, getcwd, path

import docker
import yaml
from buildbot.changes.gitpoller import GitPoller
from buildbot.config import BuilderConfig
from buildbot.plugins import steps
from buildbot.process.buildstep import BuildStep
from buildbot.process.factory import BuildFactory
from buildbot.process.properties import Interpolate
from buildbot.process.results import FAILURE, SUCCESS
from buildbot.scheduler import AnyBranchScheduler
from buildbot.schedulers.forcesched import ForceScheduler
from buildbot.schedulers.triggerable import Triggerable
from buildbot.steps.http import HTTPStep
from buildbot.steps.shell import ShellCommand
from buildbot.steps.source.base import Source
from buildbot.worker.docker import DockerLatentWorker, _handle_stream_line
from buildbot.worker.local import LocalWorker
from buildbot.www.auth import UserPasswordAuth
from buildbot.www.authz import Authz, endpointmatchers, roles
from requests.auth import HTTPBasicAuth
from twisted.internet import defer
from twisted.python import log
from twisted.python.reflect import namedModule

##########################
# Constants
##########################
LOCAL_WORKER_NAME = 'local-worker'
BOOTSTRAP_BUILDER_NAME = 'bootstrap'
BOOTSTRAP_SCHEDULER_NAME = 's-bootstrap'
TRIGGERABLE_BUILDER_NAME = 'triggerable'
TRIGGERABLE_SCHEDULER_NAME = 's-triggerable'
MAX_DOCKER_WORKERS = 10
MASTER_WEB_PORT = 8000
EVE_FOLDER = 'eve'
EVE_MAIN_YAML = 'main.yml'
EVE_MAIN_YAML_FULL_PATH = '%s/%s' % (EVE_FOLDER, EVE_MAIN_YAML)

##########################
# Set/Check environment variables
##########################
# git
GIT_REPO = environ['GIT_REPO']
assert GIT_REPO
GIT_KEY_PATH = '/root/.ssh/id_rsa'
# docker
assert 'tcp://' in environ['DOCKER_HOST']
MASTER_FQDN = os.environ['MASTER_FQDN']
if not MASTER_FQDN:
    MASTER_FQDN = os.environ['DOCKER_HOST'].replace('tcp://', '').split(':')[0]

DOCKER_CERT_PATH = environ.get('DOCKER_CERT_PATH')
DOCKER_CERT_PATH_CA = os.path.join(DOCKER_CERT_PATH, 'ca.pem')
DOCKER_CERT_PATH_KEY = os.path.join(DOCKER_CERT_PATH, 'key.pem')
DOCKER_CERT_PATH_CERT = os.path.join(DOCKER_CERT_PATH, 'cert.pem')
assert path.isdir(DOCKER_CERT_PATH), DOCKER_CERT_PATH
assert path.isfile(DOCKER_CERT_PATH_CA), DOCKER_CERT_PATH_CA
assert path.isfile(DOCKER_CERT_PATH_KEY), DOCKER_CERT_PATH_KEY
assert path.isfile(DOCKER_CERT_PATH_CERT), DOCKER_CERT_PATH_CERT

EVE_LOGIN = environ.get('EVE_LOGIN')
EVE_PWD = environ.get('EVE_PWD')
assert EVE_LOGIN
assert EVE_PWD

# database
# TODO : for prod, use something like 'mysql://user@pass:mysqlserver/buildbot'
DB_URL = environ.get('DB_URL', 'sqlite:///state.sqlite')

##########################
# Project Identity
##########################
c = BuildmasterConfig = {}
c['title'] = "Eve"
c['titleURL'] = "http://www.scality.com/"
c['buildbotURL'] = 'http://%s:%d/' % (MASTER_FQDN, MASTER_WEB_PORT)

# 'protocols' contains information about protocols which master will use for
# communicating with workers. You must define at least 'port' option that
# workers could connect to your master with this protocol.
# 'port' must match the value configured into the buildworkers (with their
# --master option)
c['protocols'] = {'pb': {'port': 9989}}


##########################
# Web UI
##########################
# Limit write operations to the developer account
class RolesFromUsername(roles.RolesFromBase):
    def __init__(self, username, role):
        self.username = username
        self.role = role

    def getRolesFromUser(self, userDetails):
        if 'username' in userDetails:
            if userDetails['username'] == self.username:
                return [self.role]
        return []

authz = Authz(
    allowRules=[
        endpointmatchers.StopBuildEndpointMatcher(role='admin'),
        endpointmatchers.ForceBuildEndpointMatcher(role='admin'),
        endpointmatchers.RebuildBuildEndpointMatcher(role='admin'),
    ],
    roleMatchers=[
        RolesFromUsername(username='developer', role='admin')
    ]
)
# Create a basic auth website with the waterfall view and the console view
c['www'] = dict(port=MASTER_WEB_PORT,
                auth=UserPasswordAuth({EVE_LOGIN: EVE_PWD}),
                authz=authz,
                plugins=dict(
                    waterfall_view={},
                    console_view={}))

# DB URL
# TODO: Replace with a MySQL database
c['db'] = {
    # This specifies what database buildbot uses to store its state.
    # You can leave this at its default for all but the largest installations.
    'db_url': DB_URL,
}

# #########################
# Reporters
# #########################
# mail / hipchat / web notifications
# c['reporters'] = []


##########################
# Workers
##########################
c['workers'] = [LocalWorker(LOCAL_WORKER_NAME)]
tls_config = docker.tls.TLSConfig(
    client_cert=(
        DOCKER_CERT_PATH_CERT,
        DOCKER_CERT_PATH_KEY),
    ca_cert=DOCKER_CERT_PATH_CA,
    verify=False)
docker_workers = []
for i in range(MAX_DOCKER_WORKERS):
    docker_workers.append(
        DockerLatentWorker(
            name='latent-docker-worker-%d' % i,
            password='pwd%d' % i,
            docker_host=environ['DOCKER_HOST'],
            tls=tls_config,
            image='build_docker_image_ubuntu-trusty-ctxt',
            networking_config=None,
            followStartupLogs=True,
            masterFQDN=MASTER_FQDN))
c['workers'].extend(docker_workers)

##########################
# Change Sources
##########################
# the 'change_source' setting tells the buildmaster how it should find out
# about source code changes.

c['change_source'] = []
c['change_source'].append(GitPoller(
    GIT_REPO,
    workdir='gitpoller-workdir',
    branches=True,
    pollinterval=60,
    pollAtLaunch=True,
    buildPushesWithNoCommits=True,
))


##########################
# Custom Build Steps
##########################
class ReadConfFromYaml(steps.SetPropertyFromCommand):
    """This step reads the YAML file and converts it to
     a 'conf' property to be available to the next steps."""

    def __init__(self, **kwargs):
        steps.SetPropertyFromCommand.__init__(
            self,
            name='Read config from %s' % EVE_MAIN_YAML_FULL_PATH,
            command='cat %s' % EVE_MAIN_YAML_FULL_PATH,
            property='conf',
            haltOnFailure=True,
            **kwargs)

    def commandComplete(self, cmd):
        if cmd.didFail():
            return
        yaml_result = yaml.load(self.observer.getStdout())
        self.setProperty(self.property, yaml_result, "ReadConfFromYaml Step")


class StepExtractor(BuildStep):
    """This step extracts the build steps from the 'conf' property and adds
    them to the current builder. It also adds a step to build an image.
    """
    name = 'step extractor'

    def run(self):
        stage_name = self.getProperty('stage_name', 'main')
        conf = self.getProperty('conf')
        stage_conf = conf['stages'][stage_name]
        docker_path = stage_conf['image']['path']
        full_docker_path = 'workers/%s/%s/build/%s/%s' % (
            LOCAL_WORKER_NAME,
            BOOTSTRAP_BUILDER_NAME,
            EVE_FOLDER,
            docker_path)

        step = BuildDockerImage(
            name=str('build_docker_image_%s' % docker_path),
            path=full_docker_path)
        self.build.addStepsAfterCurrentStep([step])
        for step in stage_conf['steps']:
            step_type, params = dict.popitem(step)
            try:
                # try to see in the required step is imported or
                # defined in the current context
                _cls = globals()[step_type]
            except:
                # otherwise import the step from standars buildbot steps
                try:
                    _cls = getattr(steps, step_type)
                except AttributeError:
                    raise Exception('Could not load step %s' % step_type)

            log.msg('%s with params : %s' % (step_type, params))

            # Add the ability to interpret properties from the command
            # parameters usually used in ShellCommand steps
            # TODO: See if we can generalize this behaviour to all parameters
            if 'command' in params:
                params['command'] = Interpolate(params['command'])

            # hack to prevent displaying passwords stored in env variables
            # on the web interface
            if issubclass(_cls, ShellCommand) or issubclass(_cls, Source):
                params['logEnviron'] = False

            # hack to avoid putting clear passwords into the YAML file
            # for the HTTP step
            if issubclass(_cls, HTTPStep):
                pwd = params['auth'][1].replace('$', '')
                if pwd in os.environ:
                    params['auth'] = HTTPBasicAuth(
                        params['auth'][0], os.environ[pwd])

            step = _cls(**params)
            self.build.addStepsAfterLastStep([step])
        return SUCCESS


class BuildDockerImage(BuildStep):
    def __init__(self, path, **kwargs):
        BuildStep.__init__(self, **kwargs)
        self.path = path
        self.haltOnFailure = True

    def start(self):
        d = self.build_docker_image()
        d.addErrback(self.failed)

    @defer.inlineCallbacks
    def build_docker_image(self):
        # Capture the output of the docker build command in a log object
        stdio = yield self.addLog('stdio')
        docker_client = docker.Client(
            base_url=environ['DOCKER_HOST'],
            tls=tls_config
        )
        stdio.addHeader('Building docker image %s fom %s\n' % (
            self.name, self.path))
        fail = False
        # assert the directory containing the dockerfile exists
        assert path.exists(self.path), \
            '%s does not exist in %s' % (self.path, getcwd())
        shutil.copy(GIT_KEY_PATH, self.path)
        for line in docker_client.build(path=self.path, tag=self.name):
            for streamline in _handle_stream_line(line):
                if 'ERROR: ' in streamline:
                    stdio.addStderr(streamline + '\n')
                    fail = True
                else:
                    stdio.addStdout(streamline + '\n')
        stdio.finish()
        if fail:
            self.finished(FAILURE)
        self.finished(SUCCESS)


class TriggerStages(steps.Trigger):
    """ This is a step that allows to start with the properties specified
        in the schedulerNames argument (tuple) instead of using the properties
        given in the set_properties/copy_properties parameters.

        This allows to give specific parameter to every scheduler.
    """

    def __init__(self, stage_names, **kwargs):
        steps.Trigger.__init__(self, schedulerNames=stage_names, **kwargs)

    def getSchedulersAndProperties(self):
        conf = self.getProperty('conf')
        return [
            (TRIGGERABLE_SCHEDULER_NAME, {
                'stage_name': stage_name,
                'conf': conf
            }) for stage_name in self.schedulerNames]


# #########################
# Bootstrap Sequence: Schedulers
# #########################
c['schedulers'] = []
c['schedulers'].append(AnyBranchScheduler(
    name=BOOTSTRAP_SCHEDULER_NAME,
    treeStableTimer=None,
    builderNames=[BOOTSTRAP_BUILDER_NAME]))

c['schedulers'].append(ForceScheduler(
    name="force-bootstrap",
    builderNames=[BOOTSTRAP_BUILDER_NAME]))

# #########################
# Bootstrap Sequence: Build step factory
# #########################
bootstrap_factory = BuildFactory()
# Check out the source
bootstrap_factory.addStep(steps.Git(
    repourl=GIT_REPO,
    mode='incremental'))
# Read conf from yaml file
bootstrap_factory.addStep(ReadConfFromYaml())
# Extract steps from conf
bootstrap_factory.addStep(StepExtractor())

# #########################
# Bootstrap Sequence: Builders
# #########################
c['builders'] = []
c['builders'].append(
    BuilderConfig(
        name=BOOTSTRAP_BUILDER_NAME,
        workernames=[LOCAL_WORKER_NAME],
        factory=bootstrap_factory))

# #########################
# Triggerable Sequence: Schedulers
# #########################
c['schedulers'].append(Triggerable(
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
c['builders'].append(
    BuilderConfig(
        name=TRIGGERABLE_BUILDER_NAME,
        workernames=[dw.name for dw in docker_workers],
        factory=triggered_factory
    ))

# #########################
# Hacks/Bugfixes
# #########################
# Hack to fix Failure: exceptions.TypeError:
# unbound method _defaultCollapseRequestFn()
# must be called with Builder instance as first
# argument (got BuildMaster instance instead)
c['collapseRequests'] = False

# Hack to fix a bug stating that LocalWorkers do not have a valid path_module
for w in c['workers']:
    w.path_module = namedModule("posixpath")
