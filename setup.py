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

from setuptools import find_packages, setup

# Besides not advised,
# https://pip.pypa.io/en/stable/user_guide/#using-pip-from-your-program
# That's the only sane way to parse requirements.txt
try: # for pip >= 10
    from pip._internal.download import PipSession
    from pip._internal.req import parse_requirements
except ImportError: # for pip <= 9.0.3
    from pip.download import PipSession
    from pip.req import parse_requirements

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
            'eve=eve.scripts.runner:main',
        ],
        'buildbot.reporters': [
            'BitbucketBuildStatusPush=eve.reporters.bitbucket:BitbucketBuildStatusPush',
            'GithubBuildStatusPush=eve.reporters.github:GithubBuildStatusPush',
        ],
        'buildbot.schedulers': [
            'EveForceScheduler=eve.schedulers.force:EveForceScheduler',
        ],
        'buildbot.steps': [
            'CancelNonTipBuild=eve.steps.cancel:CancelNonTipBuild',
            'CancelOldBuild=eve.steps.cancel:CancelOldBuild',
            'DockerBuild=eve.steps.docker_build:DockerBuild',
            'DockerCheckLocalImage=eve.steps.docker_build:DockerCheckLocalImage',
            'DockerComputeImageFingerprint=eve.steps.docker_build:DockerComputeImageFingerprint',
            'DockerPull=eve.steps.docker_build:DockerPull',
            'DockerPush=eve.steps.docker_build:DockerPush',
            'EveProperty=eve.steps.property:EveProperty',
            'EvePropertyFromCommand=eve.steps.property:EvePropertyFromCommand',
            'GetArtifactsFromStage=eve.steps.artifacts:GetArtifactsFromStage',
            'JUnitShellCommand=eve.steps.junit:JUnitShellCommand',
            'PublishCoverageReport=eve.steps.publish_coverage_report:PublishCoverageReport',
            'ReadConfFromYaml=eve.steps.yaml_parser:ReadConfFromYaml',
            'SetArtifactsName=eve.steps.artifacts:SetArtifactsName',
            'SetArtifactsPrivateURL=eve.steps.artifacts:SetArtifactsPrivateURL',
            'SetArtifactsPublicURL=eve.steps.artifacts:SetArtifactsPublicURL',
            'SetBootstrapProperty=eve.steps.property:SetBootstrapProperty',
            'SetBootstrapPropertyFromCommand=eve.steps.property:SetBootstrapPropertyFromCommand',
            'StepExtractor=eve.steps.yaml_parser:StepExtractor',
            'PatcherConfig=eve.steps.patcher:PatcherConfig',
            'TriggerStages=eve.steps.trigger_stages:TriggerStages',
            'UnregisterRedhat=eve.steps.redhat:UnregisterRedhat',
            'Upload=eve.steps.artifacts:Upload',
        ],
        'buildbot.util': [
            'BaseBuildOrder=eve.util.build_order:BaseBuildOrder',
            'BaseDockerBuildOrder=eve.util.build_order:BaseDockerBuildOrder',
            'Patcher=eve.steps.patcher:Patcher',
            'convert_to_bytes=eve.util.convert:convert_to_bytes',
            'convert_to_cpus=eve.util.convert:convert_to_cpus',
            'env=eve.util.env:SETTINGS',
            'get_local_jobs=eve.util.local_jobs:get_local_jobs',
            'hideStepIfSkipped=eve.util.step:hideStepIfSkipped',
            'hideStepIfSuccess=eve.util.step:hideStepIfSuccess',
            'hideStepIfSuccessOrSkipped=eve.util.step:hideStepIfSuccessOrSkipped',
            'isRedhat=eve.util.redhat:isRedhat',
            'load_env=eve.util.env:load_env',
            'nextBootstrapBuild=eve.util.next_bootstrap_build:nextBootstrapBuild',
            'password_generator=eve.util.password_generator:password_generator',
            'step_factory=eve.util.step_factory:step_factory',
            'verify_docker_certificates=eve.util.docker:verify_docker_certificates',
            'replace_with_interpolate=eve.util.step_factory:replace_with_interpolate',
            'create_hash=eve.util.hash:create_hash',
            'compute_instance_name=eve.util.worker:compute_instance_name',
        ],
        'buildbot.worker': [
            'EveDockerLatentWorker=eve.worker.docker.docker_worker:EveDockerLatentWorker',
            'HeatLatentWorker=eve.worker.openstack_heat.openstack_heat_worker:HeatLatentWorker',
            'EveKubeLatentWorker=eve.worker.kubernetes.kubernetes_worker:EveKubeLatentWorker',
        ]
    },
    zip_safe=False
)
