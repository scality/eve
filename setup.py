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
            'CancelNonTipBuild=eve.steps.cancel:CancelNonTipBuild',
            'CancelOldBuild=eve.steps.cancel:CancelOldBuild',
            'CloudfilesAuthenticate=eve.steps.artifacts:CloudfilesAuthenticate',
            'DockerBuild=eve.steps.docker_build:DockerBuild',
            'GetArtifactsFromStage=eve.steps.artifacts:GetArtifactsFromStage',
            'JUnitShellCommand=eve.steps.junit:JUnitShellCommand',
            'PublishCoverageReport=eve.steps.publish_coverage_report:PublishCoverageReport',
            'ReadConfFromYaml=eve.steps.yaml_parser:ReadConfFromYaml',
            'StepPatcher=eve.steps.step_patcher:StepPatcher',
            'StepPatcherConfig=eve.steps.step_patcher:StepPatcherConfig',
            'ShellCommandWithSecrets=eve.steps.shell_command_with_secrets:ShellCommandWithSecrets',
            'StepExtractor=eve.steps.yaml_parser:StepExtractor',
            'TriggerStages=eve.steps.trigger_stages:TriggerStages',
            'Upload=eve.steps.artifacts:Upload'
        ],
        'buildbot.util': [
            'BaseBuildOrder=eve.util.build_order:BaseBuildOrder',
            'env=eve.util.env:SETTINGS',
            'get_local_jobs=eve.util.local_jobs:get_local_jobs',
            'get_secrets=eve.util.env:get_secrets',
            'init_sentry_logging=eve.util.sentry:init_sentry_logging',
            'load_env=eve.util.env:load_env',
            'password_generator=eve.util.password_generator:password_generator',
            'step_factory=eve.util.step_factory:step_factory',
            'verify_docker_certificates=eve.util.docker:verify_docker_certificates'
        ],
        'buildbot.worker': [
            'EveDockerLatentWorker=eve.worker.docker.docker_worker:EveDockerLatentWorker',
            'EveOpenStackLatentWorker=eve.worker.openstack.openstack_worker:EveOpenStackLatentWorker'
        ]
    },
    zip_safe=False
)
