#!/usr/bin/env python2

# Copyright 2017 Scality
#
# This file is part of Eve.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.

from os.path import abspath, dirname, join

from pip.download import PipSession
from pip.req import parse_requirements
from setuptools import find_packages, setup

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
    packages=find_packages(where='.'),
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
            'GithubBuildStatusPush=eve.reporters.base:GithubBuildStatusPush',
            'HipChatBuildStatusPush=eve.reporters.base:HipChatBuildStatusPush',
        ],
        'buildbot.schedulers': [
            'EveForceScheduler=eve.schedulers.force:EveForceScheduler'
        ],
        'buildbot.steps': [
            'CancelNonTipBuild=eve.steps.cancel:CancelNonTipBuild',
            'CancelOldBuild=eve.steps.cancel:CancelOldBuild',
            'DockerBuild=eve.steps.docker_build:DockerBuild',
            'DockerCheckLocalImage=eve.steps.docker_build:DockerCheckLocalImage',
            'DockerComputeImageFingerprint=eve.steps.docker_build:DockerComputeImageFingerprint',
            'DockerPull=eve.steps.docker_build:DockerPull',
            'DockerPush=eve.steps.docker_build:DockerPush',
            'GetArtifactsFromStage=eve.steps.artifacts:GetArtifactsFromStage',
            'JUnitShellCommand=eve.steps.junit:JUnitShellCommand',
            'PublishCoverageReport=eve.steps.publish_coverage_report:PublishCoverageReport',
            'ReadConfFromYaml=eve.steps.yaml_parser:ReadConfFromYaml',
            'ShellCommandWithSecrets=eve.steps.shell_command_with_secrets:ShellCommandWithSecrets',
            'StepExtractor=eve.steps.yaml_parser:StepExtractor',
            'StepPatcherConfig=eve.steps.step_patcher:StepPatcherConfig',
            'TriggerStages=eve.steps.trigger_stages:TriggerStages',
            'Upload=eve.steps.artifacts:Upload'
        ],
        'buildbot.util': [
            'BaseBuildOrder=eve.util.build_order:BaseBuildOrder',
            'env=eve.util.env:SETTINGS',
            'get_local_jobs=eve.util.local_jobs:get_local_jobs',
            'get_secrets=eve.util.env:get_secrets',
            'hideStepIfSuccess=eve.util.step:hideStepIfSuccess',
            'hideStepIfSkipped=eve.util.step:hideStepIfSkipped',
            'hideStepIfSuccessOrSkipped=eve.util.step:hideStepIfSuccessOrSkipped',
            'init_sentry_logging=eve.util.sentry:init_sentry_logging',
            'load_env=eve.util.env:load_env',
            'nextBootstrapBuild=eve.util.next_bootstrap_build:nextBootstrapBuild',
            'password_generator=eve.util.password_generator:password_generator',
            'step_factory=eve.util.step_factory:step_factory',
            'verify_docker_certificates=eve.util.docker:verify_docker_certificates'
        ],
        'buildbot.worker': [
            'EveDockerLatentWorker=eve.worker.docker.docker_worker:EveDockerLatentWorker',
            'HeatLatentWorker=eve.worker.openstack_heat.openstack_heat_worker:HeatLatentWorker',
        ]
    },
    zip_safe=False
)
