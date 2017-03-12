from os import environ

from buildbot.changes.filter import ChangeFilter
from buildbot.plugins import util
from buildbot.scheduler import AnyBranchScheduler
from buildbot.schedulers.trysched import Try_Userpass

from schedulers.force import EveForceScheduler

BOOTSTRAP_SCHEDULER_NAME = 'bootstrap-scheduler'


def setup_frontend_schedulers(conf, bootstrap_builder_name, git_repo,
                              project_name):
    conf['schedulers'].append(AnyBranchScheduler(
        name=BOOTSTRAP_SCHEDULER_NAME,
        treeStableTimer=5,
        change_filter=ChangeFilter(branch_re='.+'),  # build only branches
        builderNames=[bootstrap_builder_name]))

    conf['schedulers'].append(EveForceScheduler(
        name='force',
        builderNames=[bootstrap_builder_name],
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
                                               default=git_repo),
                project=util.FixedParameter(name='project',
                                            default=project_name),
            )
        ],
    ))

    try_pwd = environ.pop('TRY_PWD')
    conf['schedulers'].append(Try_Userpass(
        name='try',
        port=environ['TRY_PORT'],
        userpass=[('try', try_pwd)],
        builderNames=[bootstrap_builder_name]))
