#!/usr/bin/env python2
from setuptools import setup, find_packages
from os.path import abspath, dirname, join
from pip.req import parse_requirements
from pip.download import PipSession


CWD = dirname(abspath(__file__))


def requires():
    reqs_file = join(CWD, 'requirements/base.in')
    reqs_install = parse_requirements(reqs_file, session=PipSession())

    return [str(ir.req) for ir in reqs_install]


setup(
    name='eve',
    description='Scality\'s automated build system',
    url='https://bitbucket.org/scality/eve',
    include_package_data=True,
    packages=find_packages(where='src'),
    package_dir={
        '': 'src'
    },
    install_requires=requires(),
    use_scm_version={
        'local_scheme': 'dirty-tag'
    },
    setup_requires=[
        'setuptools_scm'
    ],
    entry_points={
        'console_scripts': [
            'eve=eve.scripts.runner:main'
        ],
        'buildbot.reporters': [
            'BitbucketBuildStatusPush=eve.reporters.base:BitbucketBuildStatusPush',
            'HipChatBuildStatusPush=eve.reporters.base:HipChatBuildStatusPush'
        ],
        'buildbot.schedulers': [
            'EveForceScheduler=eve.schedulers.force:EveForceScheduler'
        ],
        'buildbot.steps': [
            'DockerBuild=eve.steps.docker_build:DockerBuild',
            'GetArtifactsFromStage=eve.steps.artifacts:GetArtifactsFromStage',
            'CloudfilesAuthenticate=eve.steps.artifacts:CloudfilesAuthenticate',
            'Upload=eve.steps.artifacts:Upload',
            'JUnitShellCommand=eve.steps.junit:JUnitShellCommand',
            'CancelNonTipBuild=eve.steps.cancel:CancelNonTipBuild',
            'CancelOldBuild=eve.steps.cancel:CancelOldBuild',
            'PublishCoverageReport=eve.steps.publish_coverage_report:PublishCoverageReport',
            'ShellCommandWithSecrets=eve.steps.shell_command_with_secrets:ShellCommandWithSecrets',
            'TriggerStages=eve.steps.trigger_stages:TriggerStages',
            'ReadConfFromYaml=eve.steps.yaml_parser:ReadConfFromYaml',
            'StepExtractor=eve.steps.yaml_parser:StepExtractor'
        ],
        'buildbot.util': [
            'BaseBuildOrder=eve.util.build_order:BaseBuildOrder',
            'get_local_jobs=eve.util.local_jobs:get_local_jobs',
            'get_wamp_conf=eve.util.wamp:get_wamp_conf',
            'hide_interpolatable_name=eve.util.interpolate:hide_interpolatable_name',
            'init_sentry_logging=eve.util.sentry:init_sentry_logging',
            'password_generator=eve.util.password_generator:password_generator',
            'render_interpolatable_name=eve.util.interpolate:render_interpolatable_name',
            'step_factory=eve.util.step_factory:step_factory'
        ],
        'buildbot.worker': [
            'EveDockerLatentWorker=eve.worker.docker.docker_worker:EveDockerLatentWorker',
            'EveOpenStackLatentWorker=eve.worker.openstack.openstack_worker:EveOpenStackLatentWorker'
        ]
    },
    zip_safe=False
)
