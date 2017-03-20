#!/usr/bin/env python
# coding: utf-8
"""Eve configuration file for buildbot.

This module is the core source code of eve.
It is in fact the configuration file for buildbot.
See the `Buildbot Manual`_ for more informations.

.. _Buildbot Manual:
    http://docs.buildbot.net/latest/manual/index.html
"""

from os import environ, path

import buildbot
from buildbot.config import BuilderConfig
from buildbot.plugins import schedulers
from buildbot.plugins import steps
from buildbot.process.factory import BuildFactory
from buildbot.process.results import SUCCESS

from ..steps import trigger_stages
from ..steps.yaml_parser import StepExtractor
from ..workers.docker.build_order import DockerBuildOrder
from ..workers.openstack.build_order import OpenStackBuildOrder
from .bootstrap import setup_bootstrap
from .docker_workers import setup_docker_workers
from .hacks import setup_hacks
from .openstack_workers import setup_openstack_workers
from .services import setup_reporters


# pylint: disable=too-many-arguments
def setup_backend_only(conf, master_name, max_local_workers, worker_suffix,
                       master_fqdn, local_workers, git_repo, project_name,
                       bootstrap_builder_name):

    rackspace_credentials = {
        'login': environ.pop('RAX_LOGIN', None),
        'password': environ.pop('RAX_PWD', None)
    }

    # artifacts
    cloudfiles_url = environ.pop(
        'CLOUDFILES_URL',
        'https://storage101.dfw1.clouddrive.com/v1/MossoCloudFS_984990/')
    artifacts_url = environ.pop(
        'ARTIFACTS_URL',
        'https://artifacts.devsca.com/builds')

    artifacts_prefix = environ.get(
        'ARTIFACTS_PREFIX',
        'staging-')

    steps.Upload.CLOUDFILES_URL = cloudfiles_url
    steps.Upload.ARTIFACTS_URL = artifacts_url
    steps.Upload.ARTIFACTS_PREFIX = artifacts_prefix

    ##########################
    # Latent Workers
    ##########################

    docker_builder_name = 'docker-%s' % master_name
    docker_scheduler_name = 'docker-scheduler-%s' % master_name
    openstack_builder_name = 'openstack-%s' % master_name
    openstack_scheduler_name = 'openstack-scheduler-%s' % master_name
    max_docker_workers = max_local_workers * 12
    max_openstack_workers = max_local_workers * 10

    docker_cert_path = environ.get('DOCKER_CERT_PATH', None)
    docker_tls_verify = environ.get('DOCKER_TLS_VERIFY', '0')
    if docker_tls_verify != '0':
        # Checking that docker env vars are coherent
        assert path.isfile(path.join(docker_cert_path, 'ca.pem'))
        assert path.isfile(path.join(docker_cert_path, 'key.pem'))
        assert path.isfile(path.join(docker_cert_path, 'cert.pem'))

    # Then create MAX_DOCKER_WORKERS Docker Workers that will do the real job
    _docker_workers = setup_docker_workers(
        max_docker_workers=max_docker_workers,
        worker_suffix=worker_suffix,
        master_fqdn=master_fqdn)
    conf['workers'].extend(_docker_workers)

    # Create MAX_OPENSTACK_WORKERS that will do vm jobs
    _openstack_workers = setup_openstack_workers(
        max_openstack_workers=max_openstack_workers,
        worker_suffix=worker_suffix,
        master_fqdn=master_fqdn,
        credentials=rackspace_credentials)
    conf['workers'].extend(_openstack_workers)

    trigger_stages.TriggerStages.git_repo = git_repo
    trigger_stages.TriggerStages.workers = {
        'docker': (DockerBuildOrder, docker_scheduler_name),
        'openstack': (OpenStackBuildOrder, openstack_scheduler_name)
    }

    # #########################
    # Bootstrap Sequence: Build step factory
    # #########################
    conf['builders'].append(setup_bootstrap(
        git_repo=git_repo,
        project_name=project_name,
        bootstrap_builder_name=bootstrap_builder_name,
        local_workers=local_workers,
        openstack_credentials=rackspace_credentials,
        artifacts_url=artifacts_url,
        artifacts_prefix=artifacts_prefix))

    # #########################
    # Triggerable Sequence: Schedulers
    # #########################
    conf['schedulers'].append(schedulers.Triggerable(
        name=docker_scheduler_name,
        builderNames=[docker_builder_name]))

    conf['schedulers'].append(schedulers.Triggerable(
        name=openstack_scheduler_name,
        builderNames=[openstack_builder_name]))

    # #########################
    # Triggerable Sequence: Builders
    # #########################
    for _builder, workers in (
            (docker_builder_name, _docker_workers),
            (openstack_builder_name, _openstack_workers)):
        factory = BuildFactory()
        factory.addStep(steps.CancelOldBuild())
        # Extract steps from conf
        factory.addStep(StepExtractor(
            name='extract steps from yaml',
            hideStepIf=lambda results, s: results == SUCCESS
        ))

        conf['builders'].append(
            BuilderConfig(
                name=_builder,
                workernames=[w.name for w in workers],
                factory=factory,
                collapseRequests=False,
            )
        )

    # #########################
    # Reporters
    # #########################
    # Reporters send the build status when finished
    conf['services'] = setup_reporters(
        project_name, bootstrap_builder_name,
        docker_builder_name, openstack_builder_name)

    # #########################
    # Collapsing requests
    # #########################
    conf['collapseRequests'] = False

    # #########################
    # Set global properties
    # #########################

    conf['properties'] = {
        'buildbot_version': buildbot.version
    }

    # #########################
    # Hacks/Bugfixes
    # #########################
    setup_hacks(conf)
