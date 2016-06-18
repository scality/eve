from buildbot.worker import Worker
from buildbot.scheduler import AnyBranchScheduler
from buildbot.schedulers.forcesched import ForceScheduler
from buildbot.plugins import changes  # FIXME
from buildbot.plugins import util  # FIXME
from buildbot.plugins import steps  # FIXME

# This is a sample buildmaster config file. It must be installed as
# 'master.cfg' in your buildmaster's base directory.

# This is the dictionary that the buildmaster pays attention to. We also use
# a shorter alias to save typing.
c = BuildmasterConfig = {}


# PROJECT IDENTITY
c['title'] = "Eve"
c['titleURL'] = "http://www.scality.com"

# GIT REPOSITORIES
GIT_REPOSITORIES = [
    'https://bitbucket.org/scality/test_buildbot',
]
# BUILDWORKERS

# The 'workers' list defines the set of recognized buildworkers. Each element
# is a Buildworker object, specifying a unique worker name and password.
# The same worker name and password must be configured on the worker.
c['workers'] = [Worker("example-worker", "pass")]

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
c['change_source'].append(changes.GitPoller(
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
    builderNames=["b-bootstrap"],
))

# BUILDERS

# The 'builders' list defines the Builders, which tell Buildbot how to perform
# a build:
# what steps, and which workers can execute them.  Note that any particular
# build will only take place on one worker.

factory = util.BuildFactory()
# check out the source
factory.addStep(steps.Git(repourl='git://github.com/buildbot/pyflakes.git',
                          mode='incremental'))
# run the tests (note that this will require that 'trial' is installed)
factory.addStep(steps.ShellCommand(command=["trial", "pyflakes"]))

c['builders'] = []
c['builders'].append(
    util.BuilderConfig(name="b-bootstrap",
                       workernames=["example-worker"],
                       factory=factory))

# STATUS TARGETS

# 'status' is a list of Status Targets. The results of each build will be
# pushed to these targets. buildbot/status/*.py has a variety to choose from,
# like IRC bots.

c['status'] = []

# the 'buildbotURL' string should point to the location where the buildbot's
# internal web server is visible. This typically uses the port number set in
# the 'www' entry below, but with an externally-visible host name which the
# buildbot cannot figure out without some help.

c['buildbotURL'] = "http://localhost:8020/"

# minimalistic config to activate new web UI
c['www'] = dict(port=8020,
                plugins=dict(waterfall_view={}, console_view={}))

# DB URL

c['db'] = {
    # This specifies what database buildbot uses to store its state.
    # You can leave this at its default for all but the largest installations.
    'db_url': "sqlite:///state.sqlite",
}
