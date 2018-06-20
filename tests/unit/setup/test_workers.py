"""Unit tests of `eve.setup.workers`."""

import os
import unittest

from buildbot.plugins import util

import eve.setup.workers


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
            ('ARTIFACTS_PUBLIC_URL', 'foo.bar.baz'),
            ('DOCKER_CONTAINER_MAX_CPU', '4'),
            ('DOCKER_CONTAINER_MAX_MEMORY', '4G'),
            ('EXTERNAL_PB_PORT', '12345'),
            ('GIT_SLUG', 'slug'),
            ('MASTER_FQDN', 'foo'),
            ('MAX_DOCKER_WORKERS', 3),
            ('SUFFIX', '_foo'),
        ])
        workers = eve.setup.workers.docker_workers()
        self.assertEquals(len(workers), 3)

    def test_kube_pod_workers(self):
        util.env = util.load_env([
            ('KUBE_POD_ACTIVE_DEADLINE', '3600'),
            ('KUBE_POD_MAX_CPU', '4'),
            ('KUBE_POD_MAX_MEMORY', '4G'),
            ('KUBE_POD_NAMESPACE', 'spameggbacon'),
            ('EXTERNAL_PB_PORT', '12345'),
            ('KUBE_POD_NODE_AFFINITY', 'pool:worker'),
            ('KUBE_SERVICE', 'test-service'),
            ('KUBE_SERVICE_DATA', 'test-service-data'),
            ('KUBE_SERVICE_IN_USE', 1),
            ('MASTER_FQDN', 'foo'),
            ('MICROSERVICE_GITCACHE_IN_USE', 1),
            ('MAX_KUBE_POD_WORKERS', 3),
            ('SUFFIX', '_foo'),
        ])
        workers = eve.setup.workers.kube_pod_workers()
        self.assertEquals(len(workers), 3)

    def test_openstack_mapping(self):
        provider = 'provider1'
        field = 'field1'
        value = 'value1'

        # No mapping if yaml file does not exist
        util.env = util.load_env([
            ('OS_MAPPING_FILE_PATH', '/tmp/this_mapping_file_does_not_exist'),
        ])
        res = eve.setup.workers.openstack_mapping(provider, field, value)
        self.assertEquals(res, value)

        # No mapping if yaml file is invalid
        with open('/tmp/this_mapping_file_is_invalid', 'w') as f:
            f.write("??? this content is invalid yaml\n")
        util.env = util.load_env([
            ('OS_MAPPING_FILE_PATH', '/tmp/this_mapping_file_is_invalid'),
        ])
        res = eve.setup.workers.openstack_mapping(provider, field, value)
        os.remove('/tmp/this_mapping_file_is_invalid')
        self.assertEquals(res, value)

        # Mapping checks if yaml file is valid
        with open('/tmp/this_mapping_file_is_valid', 'w') as f:
            f.write("provider1:\n")
            f.write("  - field1:\n")
            f.write("      original_value: value1\n")
            f.write("      new_value: value2\n")
        util.env = util.load_env([
            ('OS_MAPPING_FILE_PATH', '/tmp/this_mapping_file_is_valid'),
        ])
        res1 = eve.setup.workers.openstack_mapping('provider0', field, value)
        res2 = eve.setup.workers.openstack_mapping(provider, 'field0', value)
        res3 = eve.setup.workers.openstack_mapping(provider, field, 'value0')
        res4 = eve.setup.workers.openstack_mapping(provider, field, value)
        os.remove('/tmp/this_mapping_file_is_valid')
        self.assertEquals(res1, value)
        self.assertEquals(res2, value)
        self.assertEquals(res3, 'value0')
        self.assertEquals(res4, 'value2')

    def test_openstack_heat_workers(self):
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
            ('OS_MAPPING_FILE_PATH', 'foo'),
            ('OS_NETWORK_PRIVATE', 'foo'),
            ('OS_NETWORK_PUBLIC', 'foo'),
            ('OS_NETWORK_SERVICE', 'foo'),
            ('OS_PROVIDER', 'foo'),
            ('OS_REGION_NAME', 'foo'),
            ('OS_SSH_KEY', 'foo'),
            ('OS_TENANT_NAME', 'foo'),
            ('OS_USERNAME', 'foo'),
            ('SECRET_OS_PASSWORD', 'bar'),
            ('SUFFIX', '_foo'),
        ])
        workers = eve.setup.workers.openstack_heat_workers()
        self.assertEquals(len(workers), 3)
