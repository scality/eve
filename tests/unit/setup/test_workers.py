"""Unit tests of `eve.setup.workers`."""

import unittest
from io import StringIO

from buildbot.plugins import util
from mock import patch

import eve.setup.workers


class TestSetupWorkers(unittest.TestCase):
    mapping_data = u"""
provider:
  - field:
      original_value: foo
      new_value: bar
"""

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
            ('EXTERNAL_PB_PORT', '12345'),
            ('KUBE_POD_ACTIVE_DEADLINE', '3600'),
            ('KUBE_POD_GITCONFIG_CM', 'gitconfig'),
            ('KUBE_POD_MAX_CPU', '4'),
            ('KUBE_POD_MAX_MEMORY', '4G'),
            ('KUBE_POD_NAMESPACE', 'spameggbacon'),
            ('KUBE_POD_NODE_AFFINITY', 'pool:worker'),
            ('KUBE_SERVICE', 'test-service'),
            ('KUBE_SERVICE_DATA', 'test-service-data'),
            ('KUBE_SERVICE_IN_USE', 1),
            ('MASTER_FQDN', 'foo'),
            ('MAX_KUBE_POD_WORKERS', 3),
            ('SUFFIX', '_foo'),
        ])
        workers = eve.setup.workers.kube_pod_workers()
        self.assertEquals(len(workers), 3)

    @patch('eve.setup.workers.open')
    def test_openstack_mapping_nofile(self, mock_open):
        util.env = util.load_env([
            ('OS_MAPPING_FILE_PATH', 'filepath'),
        ])

        mock_open.side_effect = OSError
        res = eve.setup.workers.openstack_mapping('provider', 'field', 'foo')
        self.assertEquals(res, 'foo')

        mock_open.side_effect = IOError
        res = eve.setup.workers.openstack_mapping('provider', 'field', 'foo')
        self.assertEquals(res, 'foo')

    @patch('eve.setup.workers.open')
    def test_openstack_mapping_invalid_yaml(self, mock_open):
        util.env = util.load_env([
            ('OS_MAPPING_FILE_PATH', 'filepath'),
        ])

        mock_open.return_value = StringIO(u"not: 'yaml")
        res = eve.setup.workers.openstack_mapping('provider', 'field', 'foo')
        self.assertEquals(res, 'foo')

    @patch('eve.setup.workers.open')
    def test_openstack_mapping_no_provider(self, mock_open):
        mock_open.return_value = StringIO(self.mapping_data)
        res = eve.setup.workers.openstack_mapping('nomatch', 'field', 'foo')
        self.assertEquals(res, 'foo')

    @patch('eve.setup.workers.open')
    def test_openstack_mapping_no_field(self, mock_open):
        mock_open.return_value = StringIO(self.mapping_data)
        res = eve.setup.workers.openstack_mapping('provider', 'nomatch', 'foo')
        self.assertEquals(res, 'foo')

    @patch('eve.setup.workers.open')
    def test_openstack_mapping_no_value(self, mock_open):
        mock_open.return_value = StringIO(self.mapping_data)
        res = eve.setup.workers.openstack_mapping('provider', 'field', 'baz')
        self.assertEquals(res, 'baz')

    @patch('eve.setup.workers.open')
    def test_openstack_mapping_match(self, mock_open):
        mock_open.return_value = StringIO(self.mapping_data)
        res = eve.setup.workers.openstack_mapping('provider', 'field', 'foo')
        self.assertEquals(res, 'bar')

    def test_openstack_worker_script_with_user_script(self):
        res = eve.setup.workers.openstack_worker_script('path', 'user_data')
        self.assertEquals(res, 'user_data')

    @patch('eve.setup.workers.open')
    def test_openstack_worker_script_missing_default_file(self, mock_open):
        mock_open.side_effect = OSError
        with self.assertRaises(OSError):
            eve.setup.workers.openstack_worker_script('/path', '')

    def test_openstack_worker_script_default_script(self):
        res = eve.setup.workers.openstack_worker_script(
            'os_script_init.sh', '')
        self.assertTrue(res.startswith('#!/bin/bash'))

    @patch('eve.setup.workers.open')
    def test_openstack_worker_script_custom_script(self, mock_open):
        mock_open.return_value = StringIO(u"script contents")
        res = eve.setup.workers.openstack_worker_script('/path', '')
        self.assertEquals(res, 'script contents')
        mock_open.assert_called_once()
        self.assertEqual(mock_open.call_args_list[0][0][0], '/path')

    def test_openstack_heat_workers(self):
        util.env = util.load_env([
            ('EXTERNAL_PB_PORT', 12345),
            ('GIT_SLUG', 'slug'),
            ('MASTER_FQDN', 'foo'),
            ('MAX_OPENSTACK_WORKERS', 3),
            ('OS_AUTH_URL', 'foo'),
            ('OS_IDENTITY_API_VERSION', '2'),
            ('OS_KEY_NAME', 'bar'),
            ('OS_MAPPING_FILE_PATH', 'foo'),
            ('OS_NETWORK_PRIVATE', 'foo'),
            ('OS_NETWORK_PUBLIC', 'foo'),
            ('OS_NETWORK_SERVICE', 'foo'),
            ('OS_PASSWORD', 'bar'),
            ('OS_PROJECT_DOMAIN_ID', 'default'),
            ('OS_PROVIDER', 'foo'),
            ('OS_REGION_NAME', 'foo'),
            ('OS_SCRIPT_BOOT_FILE_PATH', 'bootscript'),
            ('OS_SCRIPT_INIT_FILE_PATH', 'initscript'),
            ('OS_SCRIPT_REQUIREMENTS_FILE_PATH', 'reqscript'),
            ('OS_SCRIPT_START_FILE_PATH', 'startscript'),
            ('OS_SSH_KEY', 'foo'),
            ('OS_TENANT_NAME', 'foo'),
            ('OS_USERNAME', 'foo'),
            ('SUFFIX', '_foo'),
        ])
        workers = eve.setup.workers.openstack_heat_workers()
        self.assertEquals(len(workers), 3)
