"""Unit tests of `eve.setup.workers`."""

import unittest

from buildbot.plugins import util
from eve.worker.docker.docker_worker import convert_to_bytes

import eve.setup.workers


class TestSetupWorkers(unittest.TestCase):
    def test_convert_to_bytes(self):
        with self.assertRaises(ValueError):
            size = convert_to_bytes('notanumber')
        size = convert_to_bytes('1234')
        self.assertEquals(size, 1234)
        size = convert_to_bytes('1B')
        self.assertEquals(size, 1)
        size = convert_to_bytes('1b')
        self.assertEquals(size, 1)
        size = convert_to_bytes('2K')
        self.assertEquals(size, 2048)
        size = convert_to_bytes('2k')
        self.assertEquals(size, 2048)
        size = convert_to_bytes('4M')
        self.assertEquals(size, 4194304)
        size = convert_to_bytes('4m')
        self.assertEquals(size, 4194304)
        size = convert_to_bytes('8G')
        self.assertEquals(size, 8589934592)
        size = convert_to_bytes('8g')
        self.assertEquals(size, 8589934592)
        size = convert_to_bytes('8gi')
        self.assertEquals(size, 8589934592)
        size = convert_to_bytes('8gb')
        self.assertEquals(size, 8589934592)

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
            ('ARTIFACTS_PUBLIC_URL', 'foo.bar.baz'),
            ('DOCKER_CONTAINER_MAX_CPU', 4),
            ('DOCKER_CONTAINER_MAX_MEMORY', '8G'),
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
            ('MICROSERVICE_ARTIFACTS_VM_URL', 'foo.bar'),
            ('MICROSERVICE_GITCACHE_VM_URL', 'foo.bar'),
            ('OS_AUTH_URL', 'foo'),
            ('OS_KEY_NAME', 'bar'),
            ('OS_NETWORK_PRIVATE', 'foo'),
            ('OS_NETWORK_PUBLIC', 'foo'),
            ('OS_NETWORK_SERVICE', 'foo'),
            ('OS_REGION_NAME', 'foo'),
            ('OS_SSH_KEY', 'foo'),
            ('OS_TENANT_NAME', 'foo'),
            ('OS_USERNAME', 'foo'),
            ('SECRET_OS_PASSWORD', 'bar'),
            ('SUFFIX', '_foo'),
        ])
        workers = eve.setup.workers.openstack_heat_workers()
        self.assertEquals(len(workers), 3)
