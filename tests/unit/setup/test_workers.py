"""Unit tests of `eve.setup.workers`."""

import unittest

import eve.setup.workers
from buildbot.plugins import util


class TestSetupWorkers(unittest.TestCase):
    def test_local_workers(self):
        util.env = util.load_env([
            ('GIT_SLUG', 'slug'),
            ('MAX_LOCAL_WORKERS', 3),
            ('SUFFIX', '_foo')
        ])
        workers = eve.setup.workers.local_workers()
        self.assertEquals(len(workers), 3)

    def test_docker_workers(self):
        util.env = util.load_env([
            ('ARTIFACTS_PREFIX', 'foo_'),
            ('DOCKER_CONTAINER_MAX_CPU', 4),
            ('DOCKER_CONTAINER_MAX_MEMORY', 4096),
            ('EXTERNAL_PB_PORT', '12345'),
            ('GIT_SLUG', 'slug'),
            ('MASTER_FQDN', 'foo'),
            ('MAX_DOCKER_WORKERS', 3),
            ('SUFFIX', '_foo'),
        ])
        workers = eve.setup.workers.docker_workers()
        self.assertEquals(len(workers), 3)

    def test_openstack_workers(self):
        util.env = util.load_env([
            ('CLOUD_INIT_SCRIPT', 'foo'),
            ('EXTERNAL_PB_PORT', 12345),
            ('GIT_SLUG', 'slug'),
            ('MASTER_FQDN', 'foo'),
            ('MAX_OPENSTACK_WORKERS', 3),
            ('OS_AUTH_URL', 'foo'),
            ('OS_KEY_NAME', 'bar'),
            ('OS_REGION_NAME', 'foo'),
            ('OS_SSH_KEY', 'foo'),
            ('OS_TENANT_NAME', 'foo'),
            ('OS_USERNAME', 'foo'),
            ('SECRET_OS_PASSWORD', 'bar'),
            ('SUFFIX', '_foo'),
        ])
        workers = eve.setup.workers.openstack_workers()
        self.assertEquals(len(workers), 3)
