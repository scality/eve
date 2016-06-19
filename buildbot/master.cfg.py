import os

import yaml
import buildbot.plugins
from buildbot.plugins import util
from buildbot.process.buildstep import BuildStep
from buildbot.scheduler import AnyBranchScheduler
from buildbot.schedulers.forcesched import ForceScheduler
from buildbot.schedulers.triggerable import Triggerable
from buildbot.steps.shell import SetPropertyFromCommand
from buildbot.steps.trigger import Trigger
from buildbot.worker.local import LocalWorker
from twisted.python.reflect import namedModule

# GIT REPO
GIT_REPO = os.environ['GIT_REPO']
assert GIT_REPO


# CODE

class ReadConfFromYaml(SetPropertyFromCommand):
    def __init__(self, **kwargs):
        SetPropertyFromCommand.__init__(
            self,
            name='add steps from yaml',
            command='cat .buildbot/main.yaml',
            property='conf',
            **kwargs)

    def commandComplete(self, cmd):
        if cmd.didFail():
            return
        result = self.observer.getStdout()
        yresult = yaml.load(result)
        self.setProperty(self.property, yresult, "SetPropertyFromCommand Step")


class StepExtractor(BuildStep):
    name = 'step extractor'

    def run(self):
        stage_name = self.getProperty('stage_name', 'main')
        conf = self.getProperty('conf')
        assert conf is not None
        stage_conf = conf['stages'][stage_name]
        steps = stage_conf['steps']
        for step in reversed(steps):
            assert len(step) == 1
            step_type, params = dict.popitem(step)
            try:
                _cls = globals()[step_type]
            except:
                _cls = getattr(buildbot.steps.shell, step_type)
            step = _cls(**params)
            self.build.addStepsAfterCurrentStep([step])
        return util.SUCCESS


class TriggerStages(Trigger):
    """ This is a step that allows to start with the properties specified
        in the schedulerNames argument (tuple) instead of using the properties
        given in the set_properties/copy_properties parameters.

        This allows to give specific parameter to every scheduler.
    """

    def __init__(self, stage_names, **kwargs):
        # self.stage_names = stage_names
        Trigger.__init__(self, schedulerNames=stage_names, **kwargs)

    def getSchedulersAndProperties(self):
        conf = self.getProperty('conf')
        assert conf
        return [
            ('s-triggerable', {
                'stage_name': stage_name,
                'conf': conf
            }) for stage_name in self.schedulerNames]


# BUILDBOT CONFIGURATION

# This is the dictionary that the buildmaster pays attention to. We also use
# a shorter alias to save typing.
c = BuildmasterConfig = {}

# PROJECT IDENTITY
c['title'] = "Eve"
c['titleURL'] = "http://www.scality.com"
c['buildbotURL'] = "http://localhost:8020/"

# BUILDWORKERS
# The 'workers' list defines the set of recognized buildworkers. Each element
# is a Buildworker object, specifying a unique worker name and password.
# The same worker name and password must be configured on the worker.
c['workers'] = [
    LocalWorker('local-worker1'),
    LocalWorker('local-worker2'),
]

# The following lines are a workaround for a bug
for w in c['workers']:
    w.path_module = namedModule("posixpath")

# 'protocols' contains information about protocols which master will use for
# communicating with workers. You must define at least 'port' option that
# workers could connect to your master with this protocol.
# 'port' must match the value configured into the buildworkers (with their
# --master option)
c['protocols'] = {'pb': {'port': 9989}}

# CHANGESOURCES

# the 'change_source' setting tells the buildmaster how it should find out
# about source code changes.  Here we point to the buildbot clone of pyflakes.

c['change_source'] = []
c['change_source'].append(buildbot.plugins.changes.GitPoller(
    'git://github.com/buildbot/pyflakes.git',
    workdir='gitpoller-workdir', branch='master',
    pollinterval=300))

# SCHEDULERS

# Configure the Schedulers, which decide how to react to incoming changes.
# In this case, just kick off a 'runtests' build

c['schedulers'] = []
c['schedulers'].append(AnyBranchScheduler(
    name="s-bootstrap",
    treeStableTimer=None,
    builderNames=["b-bootstrap"]))

c['schedulers'].append(ForceScheduler(
    name="force",
    builderNames=["b-bootstrap"]))

c['schedulers'].append(Triggerable(
    name="s-triggerable",
    builderNames=["b-triggerable"]))

# BUILDERS

# The 'builders' list defines the Builders, which tell Buildbot how to perform
# a build:
# what steps, and which workers can execute them.  Note that any particular
# build will only take place on one worker.

bootstrap_factory = util.BuildFactory()
# check out the source
bootstrap_factory.addStep(
    buildbot.plugins.steps.Git(repourl=GIT_REPO, mode='incremental'),
)
bootstrap_factory.addStep(ReadConfFromYaml())
bootstrap_factory.addStep(StepExtractor())

# bootstrap_factory.addStep(YamlStepGenerator(
#    name="parse main.yaml",
#    command=["cat", ".buildbot/main.yaml"],
#    haltOnFailure=True)
# )

triggered_factory = util.BuildFactory()
triggered_factory.addStep(StepExtractor())

c['builders'] = []
c['builders'].append(
    util.BuilderConfig(name="b-bootstrap",
                       workernames=['local-worker1', 'local-worker2'],
                       factory=bootstrap_factory))

c['builders'].append(
    util.BuilderConfig(
        name="b-triggerable",
        workernames=['local-worker1', 'local-worker2'],
        # nextSlave=latent_worker_chooser,
        factory=triggered_factory
    ))
# STATUS TARGETS

# 'status' is a list of Status Targets. The results of each build will be
# pushed to these targets. buildbot/status/*.py has a variety to choose from,
# like IRC bots.

c['status'] = []

# minimalistic config to activate new web UI
c['www'] = dict(port=8020,
                plugins=dict(waterfall_view={}, console_view={}))

# DB URL

c['db'] = {
    # This specifies what database buildbot uses to store its state.
    # You can leave this at its default for all but the largest installations.
    'db_url': "sqlite:///state.sqlite",
}


@util.renderer
def get_bitbucket_url_with_credentials(props):
    repo_url = props.getProperty('repository')
    return repo_url.replace('https://bitbucket.org/', 'git@bitbucket.org:')
