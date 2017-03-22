from buildbot.config import BuilderConfig
from buildbot.plugins import steps
from buildbot.process.factory import BuildFactory
from buildbot.process.results import SUCCESS


def triggerable_builder(builder_name, workers):
    factory = BuildFactory()
    factory.addStep(steps.CancelOldBuild())
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
