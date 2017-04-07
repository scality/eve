from buildbot.changes.filter import ChangeFilter
from buildbot.plugins import schedulers, util
from buildbot.scheduler import AnyBranchScheduler
from buildbot.schedulers.triggerable import Triggerable
from buildbot.schedulers.trysched import Try_Userpass


def any_branch_scheduler():
    return AnyBranchScheduler(
        name=util.env.BOOTSTRAP_SCHEDULER_NAME,
        treeStableTimer=5,
        change_filter=ChangeFilter(branch_re='.+'),  # build only branches
        builderNames=[util.env.BOOTSTRAP_BUILDER_NAME])


def force_scheduler():
    default_project = "%s/%s" % (
        util.env.GIT_OWNER, util.env.GIT_SLUG)
    return schedulers.EveForceScheduler(
        name=util.env.FORCE_SCHEDULER_NAME,
        builderNames=[util.env.BOOTSTRAP_BUILDER_NAME],
        reason=util.StringParameter(name='reason',
                                    label='Reason:',
                                    default='force build',
                                    size=20),
        codebases=[
            util.CodebaseParameter(
                '',
                branch=util.StringParameter(name='branch',
                                            label='Branch:',
                                            required=True),
                revision=util.FixedParameter(name='revision',
                                             default=''),
                repository=util.FixedParameter(name='repository',
                                               default=util.env.GIT_REPO),
                project=util.FixedParameter(name='project',
                                            default=default_project),
            )
        ]
    )


def try_scheduler():
    return Try_Userpass(
        name=util.env.TRY_SCHEDULER_NAME,
        port=util.env.TRY_PORT,
        userpass=[('try', util.env.TRY_PWD)],
        builderNames=[util.env.BOOTSTRAP_BUILDER_NAME])


def triggerable_scheduler(scheduler_name, builder_name):
    return Triggerable(
        name=scheduler_name,
        builderNames=[builder_name])
