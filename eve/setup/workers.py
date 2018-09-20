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

from collections import namedtuple
from os.path import abspath, dirname, join

import yaml
from buildbot import version
from buildbot.plugins import util, worker
from buildbot.process.properties import Interpolate, Property, Transform
from buildbot.worker.local import LocalWorker
from twisted.logger import Logger
from twisted.python.reflect import namedModule


def local_workers():
    workers = []
    for i in range(util.env.MAX_LOCAL_WORKERS):
        worker_ = LocalWorker('lw%03d-%s' % (
            i, util.env.SUFFIX))
        # Hack to fix a bug stating that LocalWorkers
        # do not have a valid path_module
        worker_.path_module = namedModule('posixpath')
        workers.append(worker_)
    return workers


def docker_workers():
    workers = []
    for i in range(util.env.MAX_DOCKER_WORKERS):
        workers.append(
            worker.EveDockerLatentWorker(
                name='dw%03d-%s' % (i, util.env.SUFFIX),
                password=util.password_generator(),
                master_fqdn=util.env.MASTER_FQDN,
                pb_port=util.env.EXTERNAL_PB_PORT,
                max_memory=util.env.DOCKER_CONTAINER_MAX_MEMORY,
                max_cpus=util.env.DOCKER_CONTAINER_MAX_CPU,
                image=Property('docker_image'),
                keepalive_interval=300,
            ))
    return workers


def kube_pod_workers():
    workers = []
    NodeAffinity = namedtuple('NodeAffinity', ('key', 'value'))
    node_affinity = None
    if util.env.KUBE_POD_NODE_AFFINITY:
        node_affinity = NodeAffinity(
            *util.env.KUBE_POD_NODE_AFFINITY.split(':'))

    service = ''
    service_data = ''
    if util.env.KUBE_SERVICE_IN_USE:
        service = util.env.KUBE_SERVICE
        service_data = util.env.KUBE_SERVICE_DATA
        assert service

    for i in range(util.env.MAX_KUBE_POD_WORKERS):
        workers.append(
            worker.EveKubeLatentWorker(
                'kw%03d-%s' % (i, util.env.SUFFIX),
                password=util.password_generator(),
                master_fqdn=util.env.MASTER_FQDN,
                pb_port=util.env.EXTERNAL_PB_PORT,
                namespace=util.env.KUBE_POD_NAMESPACE,
                node_affinity=node_affinity,
                max_memory=util.env.KUBE_POD_MAX_MEMORY,
                max_cpus=util.env.KUBE_POD_MAX_CPU,
                microservice_gitcache=util.env.MICROSERVICE_GITCACHE_IN_USE,
                kube_config=None,
                keepalive_interval=300,
                active_deadline=util.env.KUBE_POD_ACTIVE_DEADLINE,
                service=service,
                service_data=service_data,
            ))
    return workers


START_WORKER_SCRIPT = """
sudo -iu eve git config --global \
  url.http://{gitcache_host}/https/bitbucket.org/.insteadOf \
  git@bitbucket.org:
sudo -iu eve git config --global \
  url.http://{gitcache_host}/https/github.com/.insteadOf \
  git@github.com:
sudo -iu eve buildbot-worker create-worker --umask=022 /home/eve/worker \
"{master_fqdn}:{master_port}" {worker_name} "{worker_password}"
sudo -iu eve buildbot-worker start /home/eve/worker
"""


def openstack_mapping(provider, field, value):
    logger = Logger('eve.setup.workers')

    mapping = {}
    mapping_path = util.env.OS_MAPPING_FILE_PATH

    try:
        with open(mapping_path) as mapping_file:
            mapping = yaml.load(mapping_file.read())
    except (OSError, IOError, yaml.YAMLError) as err:
        logger.error('An error occured while loading the mapping file at '
                     '{path}: {err}', path=mapping_path, err=err)
        return value

    try:
        for chunk in mapping.get(provider, []):
            field_section = chunk.get(field, None)

            if field_section:
                original_value = field_section.get('original_value', None)
                new_value = field_section.get('new_value', None)

                if original_value == value and new_value is not None:
                    return new_value
    except AttributeError as err:
        logger.error('An error occured while parsing the mapping file at '
                     '{path}: {err}', path=mapping_path, err=err)

    return value


def openstack_heat_workers():
    workers = []
    heat_template = open(join(dirname(abspath(__file__)),
                              'single_node_heat_template.yml')).read()

    for i in range(util.env.MAX_OPENSTACK_WORKERS):
        name = 'hw%03d-%s' % (i, util.env.SUFFIX)
        password = util.password_generator()

        start_worker_script = Interpolate(START_WORKER_SCRIPT.format(
            gitcache_host=util.env.MICROSERVICE_GITCACHE_VM_URL,
            master_fqdn=util.env.MASTER_FQDN,
            master_port=util.env.EXTERNAL_PB_PORT,
            worker_name=name,
            worker_password=password,
        ))

        workers.append(
            worker.HeatLatentWorker(
                name=name,
                password=password,
                heat_template=heat_template,
                heat_template_parameters={
                    'image': Transform(openstack_mapping,
                                       provider=util.env.OS_PROVIDER,
                                       field="image",
                                       value=Property('openstack_image')),
                    'flavor': Transform(openstack_mapping,
                                        provider=util.env.OS_PROVIDER,
                                        field="flavor",
                                        value=Property('openstack_flavor')),
                    'key_name': util.env.OS_KEY_NAME,
                    'public_network': util.env.OS_NETWORK_PUBLIC,
                    'service_network': util.env.OS_NETWORK_SERVICE,
                    'private_network': util.env.OS_NETWORK_PRIVATE,
                    'worker_version': version,
                    'worker_init_script': Property('init_script'),
                    'worker_requirements_script': Property(
                        'requirements_script'),
                    'start_worker_script': start_worker_script,
                },
                os_auth_url=util.env.OS_AUTH_URL,
                os_identity_api_version=util.env.OS_IDENTITY_API_VERSION,
                os_username=util.env.OS_USERNAME,
                os_password=util.env.OS_PASSWORD,
                os_project_domain_id=util.env.OS_PROJECT_DOMAIN_ID,
                os_project_name=util.env.OS_TENANT_NAME,
                os_region_name=util.env.OS_REGION_NAME,
                build_wait_timeout=0,  # do not reuse the stack
                keepalive_interval=300
            ))
    return workers
