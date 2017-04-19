from buildbot.config import BuilderConfig
from buildbot.plugins import steps, util
from buildbot.process.factory import BuildFactory
from buildbot.process.results import SUCCESS
from buildbot.steps.shell import ShellCommand


def triggerable_builder(builder_name, workers):
    factory = BuildFactory()
    factory.addStep(steps.CancelOldBuild())

    # customize global Git conf to hit on docker cache
    if builder_name == util.env.DOCKER_BUILDER_NAME:
        factory.addStep(ShellCommand(
            name='customize git settings to hit on cache',
            hideStepIf=lambda results, s: results == SUCCESS,
            haltOnFailure=True,

            command='git config --global '
                    'url.http://git_cache/https/bitbucket.org/.insteadOf '
                    'git@bitbucket.org: && '
                    'git config --global '
                    'url.http://git_cache/https/github.com/.insteadOf '
                    'git@github.com: && '
                    'git config --global '
                    'url.http://git_cache/git/mock/.insteadOf git@mock:'
        ))

    # Extract steps from conf
    factory.addStep(steps.StepExtractor(
        name='extract steps from yaml',
        hideStepIf=lambda results, s: results == SUCCESS
    ))

    return BuilderConfig(
        name=builder_name,
        workernames=[w.name for w in workers],
        factory=factory,
        collapseRequests=False)
