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

import codecs

try:
    from kubernetes import client
    from kubernetes import config as kube_config
except ImportError:
    client = None
from kubernetes.client.rest import ApiException

from tests.util.cluster import Cluster


class KubeCluster(Cluster):

    def __init__(self, *args, **kwargs):
        super(KubeCluster, self).__init__(*args, **kwargs)
        self.load_config()
        self.kube_client = client

    def load_config(self):
        try:
            kube_config.load_incluster_config()
        except Exception:
            kube_config.load_kube_config()

    def create_secret(self, name, data):
        try:
            # pylint: disable=too-many-function-args
            self.kube_client.CoreV1Api().delete_namespaced_secret(
                name, 'default', self.kube_client.V1DeleteOptions())
        except ApiException:
            pass

        for key in data.keys():
            data[key] = codecs.encode(
                data[key].encode('utf-8'), encoding='base64'
            )[:-1].decode('utf-8')

        body = {
            'api_version': 'v1',
            'kind': 'Secret',
            'type': 'Opaque',
            'metadata': {'name': 'fake-service-data'},
            'data': data,
        }
        self.kube_client.CoreV1Api().create_namespaced_secret('default', body)

    def delete_config_map(self, name):
        try:
            # pylint: disable=too-many-function-args
            self.kube_client.CoreV1Api().delete_namespaced_config_map(
                name, 'default', self.kube_client.V1DeleteOptions())
        except ApiException:
            pass

    def delete_secret(self, name):
        try:
            # pylint: disable=too-many-function-args
            self.kube_client.CoreV1Api().delete_namespaced_secret(
                name, 'default', self.kube_client.V1DeleteOptions())
        except ApiException:
            pass

    def get_config_map(self, name):
        return self.kube_client.CoreV1Api().read_namespaced_config_map(
            name, 'default')

    def get_pod(self, name):
        return self.kube_client.CoreV1Api().read_namespaced_pod(
            name, 'default')

    def get_secret(self, name):
        return self.kube_client.CoreV1Api().read_namespaced_secret(
            name, 'default')
