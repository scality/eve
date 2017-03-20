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
        'buildbot.steps': [
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
        ]
    },
    zip_safe=False
)
