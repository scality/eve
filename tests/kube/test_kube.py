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

import time
import unittest
from os import pardir
from os.path import abspath, join

from kubernetes.client.rest import ApiException
from tests.kube.cluster import KubeCluster as Cluster

from eve.worker.kubernetes.kubernetes_worker import kube_hash


class TestKube(unittest.TestCase):
    @unittest.skip('cannot run to completion until '
                   'we have an eve deployed in kube during tests')
    def test_simple_success_in_kube(self):
        """Test a successful build success with a kubernetes worker.

        Steps:
            - Force a build
            - Check that the build succeeds

        """
        conf = {
            'KUBE_POD_WORKER_IN_USE': '1',
        }
        with Cluster(extra_conf=conf) as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=abspath(
                    join(__file__, pardir, 'yaml', 'simple', 'main.yml')),
                dirs=[
                    abspath(join(__file__, pardir, 'contexts', 'simple'))
                ])
            cluster.sanity_check()
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'success')
            cluster.sanity_check()

    @unittest.skip('cannot run to completion until '
                   'we have an eve deployed in kube during tests')
    def test_fail_docker_run_in_kube(self):
        """Test a bad docker worker failing on CMD.

        Steps:
            - Force a build
            - Check that the build fails

        """
        with Cluster() as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=abspath(
                    join(__file__, pardir, 'yaml',
                         'docker_run_error', 'main.yml')),
                dirs=[
                    abspath(join(__file__, pardir, 'contexts',
                                 'docker_exit_1'))
                ])
            cluster.sanity_check()
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'exception')

    def test_incorrect_kube_yaml(self):
        """Test a build fails when incorrect yaml is provided to kube.

        Steps:
            - Force a build
            - Check that the build fails

        """
        conf = {
            'KUBE_POD_WORKER_IN_USE': '1',
        }
        with Cluster(extra_conf=conf) as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=abspath(
                    join(__file__, pardir, 'yaml', 'erroneous', 'main.yml')),
                dirs=[
                    abspath(join(__file__, pardir, 'contexts', 'simple'))
                ])
            cluster.sanity_check()
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'exception')

    @unittest.skip('cannot run to completion until '
                   'we have an eve deployed in kube during tests')
    def test_buildpath_docker_image(self):
        """Test a build success with a dockerfile path different from context.

        Steps:
            - Force a build
            - Check that the build succeed

        """
        conf = {
            'KUBE_POD_WORKER_IN_USE': '1',
        }
        with Cluster(extra_conf=conf) as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=abspath(
                    join(__file__, pardir, 'yaml', 'buildpath', 'main.yml')),
                dirs=[
                    abspath(join(__file__, pardir, 'contexts', 'simple'))
                ])
            cluster.sanity_check()
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'success')

    def test_buildpath_docker_image_failure(self):
        """Test a build failure with a dockerfile path different from context.

        Steps:
            - Force a build with an error on the kube_pod worker
            - Check that the build fails

        """
        conf = {
            'KUBE_POD_WORKER_IN_USE': '1',
        }
        with Cluster(extra_conf=conf) as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=abspath(
                    join(__file__, pardir, 'yaml', 'path_fail', 'main.yml')),
                dirs=[
                    abspath(join(__file__, pardir, 'contexts', 'simple'))
                ])
            cluster.sanity_check()
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'exception')

    @unittest.skip('cannot run to completion until '
                   'we have an eve deployed in kube during tests')
    def test_kube_yaml_OK_with_fake_service(self):
        """Test a build with correct pod and fake service.

        Steps:
            - configure eve to provide a kube service
            - Provide the service data in a config map
            - Force a build with a stage that uses a pod+service
              (the build also pre-builds the fake service image)
            - Check the service init, teardown and the build itself
              (the init and teardown script will check that
              Eve passed the correct information and fail otherwise)

        """
        conf = {
            'KUBE_POD_WORKER_IN_USE': '1',
            'KUBE_SERVICE': 'fake-service:testing',
            'KUBE_SERVICE_DATA': 'fake-service-data',
            'KUBE_SERVICE_IN_USE': '1',
            'MAX_KUBE_POD_WORKERS': '1',
        }
        with Cluster(extra_conf=conf) as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=abspath(join(
                    __file__, pardir, 'yaml',
                    'simple_with_service', 'main.yml')),
                dirs=[
                    abspath(join(__file__, pardir, 'contexts', 'simple'))
                ])
            cluster.sanity_check()

            # a bit of cleanup first
            cluster.delete_secret('fake-service-data')
            cluster.delete_config_map('fake-service-init-status')
            cluster.delete_config_map('fake-service-teardown-status')

            # check uuid secret is present if service teardown fails
            cluster.create_secret('fake-service-data', {
                'EXPECTED_KEY': 'expected_value',
                # configure behaviour of service:
                'TEST_FORCE_INIT_STATUS': '0',
                'TEST_FORCE_TEARDOWN_STATUS': '1'})
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'success')
            # get the kube workername and resolve corresponding uuid
            # (repository name changes with every run of the test)
            child_build = cluster.api.get_builds('kube_pod-test_suffix')[0]
            props = cluster.api.get_build_properties(child_build)
            uuid = kube_hash(props['repository'][0], 'kw000-test_suffix')
            self.assertEqual(cluster.get_config_map(
                'fake-service-init-status').data['status'], '0')
            self.assertEqual(cluster.get_config_map(
                'fake-service-teardown-status').data['status'], '1')
            self.assertEqual(cluster.get_secret(
                uuid).data['kubeconfig'],
                'somecredentials'.encode('base64')[:-1])
            cluster.delete_secret(uuid)
            # also check all pods are properly cleaned away
            with self.assertRaises(ApiException):
                cluster.get_pod('worker-1-1-service-init')
            with self.assertRaises(ApiException):
                cluster.get_pod('worker-1-1')
            with self.assertRaises(ApiException):
                cluster.get_pod('worker-1-1-service-teardown')
            cluster.sanity_check()

            self.assertEqual(
                props['mynamespace1'],
                kube_hash(props['repository'][0], 'mynamespace1', 1, 3)
            )
            self.assertEqual(
                props['mynamespace2'],
                kube_hash(props['repository'][0], 'mynamespace2', 1, 3)
            )

            # a bit of cleanup last
            cluster.delete_secret('fake-service-data')
            cluster.delete_config_map('fake-service-init-status')
            cluster.delete_config_map('fake-service-teardown-status')

    def test_incorrect_kube_yaml_with_fake_service(self):
        """Test a build with incorrect pod and fake service.

        Steps:
            - configure eve to provide a kube service
            - Provide the service data in a config map
            - Force a new build
            - Check that the build fails (erroneous pod definition)
            - Check that the service init and teardown ran successfully
              (the init and teardown script will check that
              Eve passed the correct information and fail otherwise)

        """
        conf = {
            'KUBE_POD_WORKER_IN_USE': '1',
            'KUBE_SERVICE': 'fake-service:testing',
            'KUBE_SERVICE_DATA': 'fake-service-data',
            'KUBE_SERVICE_IN_USE': '1',
            'MAX_KUBE_POD_WORKERS': '1',
        }
        with Cluster(extra_conf=conf) as cluster:
            local_repo = cluster.clone()
            local_repo.push(
                yaml=abspath(join(
                    __file__, pardir, 'yaml',
                    'erroneous_with_service', 'main.yml')),
                dirs=[
                    abspath(join(__file__, pardir, 'contexts', 'simple'))
                ])
            cluster.sanity_check()

            # a bit of cleanup first
            cluster.delete_secret('fake-service-data')
            cluster.delete_config_map('fake-service-init-status')
            cluster.delete_config_map('fake-service-teardown-status')

            # check what happens if service init fails
            cluster.create_secret('fake-service-data', {
                'EXPECTED_KEY': 'expected_value',
                # configure behaviour of service:
                'TEST_FORCE_INIT_STATUS': '1',
                'TEST_FORCE_TEARDOWN_STATUS': '0'})
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'exception')
            # get the kube workername and resolve corresponding uuid
            # (repository name changes with every run of the test)
            child_build = cluster.api.get_builds('kube_pod-test_suffix')[0]
            props = cluster.api.get_build_properties(child_build)
            uuid = kube_hash(props['repository'][0], 'kw000-test_suffix')
            self.assertEqual(cluster.get_config_map(
                'fake-service-init-status').data['status'], '1')
            time.sleep(5)  # teardown runs in background
            self.assertEqual(cluster.get_config_map(
                'fake-service-teardown-status').data['status'], '0')
            with self.assertRaises(ApiException):
                cluster.get_secret(uuid)
            cluster.delete_config_map('fake-service-init-status')
            cluster.delete_config_map('fake-service-teardown-status')
            # also check all pods are properly cleaned away
            with self.assertRaises(ApiException):
                cluster.get_pod('worker-1-1-service-init')
            with self.assertRaises(ApiException):
                cluster.get_pod('worker-1-1')
            with self.assertRaises(ApiException):
                cluster.get_pod('worker-1-1-service-teardown')

            # check what happens if service teardown fails
            cluster.create_secret('fake-service-data', {
                'EXPECTED_KEY': 'expected_value',
                # configure behaviour of service:
                'TEST_FORCE_INIT_STATUS': '0',
                'TEST_FORCE_TEARDOWN_STATUS': '1'})
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'exception')
            # get the kube workername and resolve corresponding uuid
            # (repository name changes with every run of the test)
            child_build = cluster.api.get_builds('kube_pod-test_suffix')[0]
            props = cluster.api.get_build_properties(child_build)
            uuid = kube_hash(props['repository'][0], 'kw000-test_suffix')
            self.assertEqual(cluster.get_config_map(
                'fake-service-init-status').data['status'], '0')
            time.sleep(5)  # teardown runs in background
            self.assertEqual(cluster.get_config_map(
                'fake-service-teardown-status').data['status'], '1')
            self.assertEqual(cluster.get_secret(
                uuid).data['kubeconfig'],
                'somecredentials'.encode('base64')[:-1])
            cluster.delete_secret(uuid)
            cluster.delete_config_map('fake-service-init-status')
            cluster.delete_config_map('fake-service-teardown-status')
            # also check all pods are properly cleaned away
            with self.assertRaises(ApiException):
                cluster.get_pod('worker-2-2-service-init')
            with self.assertRaises(ApiException):
                cluster.get_pod('worker-2-2')
            with self.assertRaises(ApiException):
                cluster.get_pod('worker-2-2-service-teardown')

            # check uuid secret is gone if service init/teardown succeed
            cluster.create_secret('fake-service-data', {
                'EXPECTED_KEY': 'expected_value',
                # configure behaviour of service:
                'TEST_FORCE_INIT_STATUS': '0',
                'TEST_FORCE_TEARDOWN_STATUS': '0'})
            buildset = cluster.api.force(branch=local_repo.branch)
            self.assertEqual(buildset.result, 'exception')
            # get the kube workername and resolve corresponding uuid
            # (repository name changes with every run of the test)
            child_build = cluster.api.get_builds('kube_pod-test_suffix')[0]
            props = cluster.api.get_build_properties(child_build)
            uuid = kube_hash(props['repository'][0], 'kw000-test_suffix')
            self.assertEqual(cluster.get_config_map(
                'fake-service-init-status').data['status'], '0')
            time.sleep(5)  # teardown runs in background
            self.assertEqual(cluster.get_config_map(
                'fake-service-teardown-status').data['status'], '0')
            with self.assertRaises(ApiException):
                cluster.get_secret(uuid)
            cluster.delete_config_map('fake-service-init-status')
            cluster.delete_config_map('fake-service-teardown-status')
            # also check all pods are properly cleaned away
            with self.assertRaises(ApiException):
                cluster.get_pod('worker-3-3-service-init')
            with self.assertRaises(ApiException):
                cluster.get_pod('worker-3-3')
            with self.assertRaises(ApiException):
                cluster.get_pod('worker-3-3-service-teardown')

            # a bit of cleanup last
            cluster.delete_secret('fake-service-data')
            cluster.delete_config_map('fake-service-init-status')
            cluster.delete_config_map('fake-service-teardown-status')
