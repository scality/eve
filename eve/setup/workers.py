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
from buildbot.process.properties import Property, Transform
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
                gitconfig=util.env.KUBE_POD_GITCONFIG_CM,
                kube_config=None,
                keepalive_interval=300,
                active_deadline=util.env.KUBE_POD_ACTIVE_DEADLINE,
                service=service,
                service_data=service_data,
            ))
    return workers


def openstack_mapping(provider, field, value, region=None):
    logger = Logger('eve.setup.workers')

    mapping = {}
    mapping_path = util.env.OS_MAPPING_FILE_PATH

    def error_openstack_mapping(err):
        logger.error('An error occured while loading the mapping file at '
                     '{path}: {err}', path=mapping_path, err=err)

    if region:
        provider_id = '{0}_{1}'.format(provider, region)
    else:
        provider_id = provider
    try:
        with open(mapping_path) as mapping_file:
            mapping = yaml.load(mapping_file.read())
    except (OSError, IOError, yaml.YAMLError) as err:
        error_openstack_mapping(err)
        return value

    try:
        provider_map = mapping[provider_id]
    except KeyError:
        try:
            provider_map = mapping[provider]
        except KeyError:
            provider_map = []

    for chunk in provider_map:
        try:
            field_section = chunk.get(field, None)
        except AttributeError as err:
            error_openstack_mapping(err)
            break
        if not field_section:
            continue

        try:
            original_value = field_section['original_value']
            new_value = field_section['new_value']
        except (AttributeError, KeyError) as err:
            error_openstack_mapping(err)
            break
        if original_value == value and new_value is not None:
            return new_value
    return value


def openstack_worker_script(default_script_path, user_script_contents):
    """Render initialization script at build time.

    The source of the script is selected according to the following rules:
    - if the worker path contains the script, use it
    - else, use the default script

    The default script location can be customised in settings.

    """
    logger = Logger('eve.setup.workers')

    if user_script_contents:
        return user_script_contents

    try:
        with open(join(dirname(dirname(abspath(__file__))), 'bin',
                  default_script_path)) as script:
            contents = script.read()
    except (OSError, IOError) as err:
        logger.error('An error occured while loading the default script file '
                     '{path}: {err}', path=default_script_path, err=err)
        raise

    return contents


def openstack_heat_workers():
    workers = []
    template = open(join(dirname(dirname(abspath(__file__))), 'etc',
                         'single_node_heat_template.yml')).read()

    params = {
        'flavor': Transform(
            openstack_mapping,
            provider=util.env.OS_PROVIDER,
            field="flavor",
            value=Property('openstack_flavor'),
            region=util.env.OS_REGION_NAME),
        'image': Transform(
            openstack_mapping,
            provider=util.env.OS_PROVIDER,
            field="image",
            value=Property('openstack_image'),
            region=util.env.OS_REGION_NAME),
        'key_name': util.env.OS_KEY_NAME,
        'master_fqdn': util.env.MASTER_FQDN,
        'master_port': util.env.EXTERNAL_PB_PORT,
        'network_private': util.env.OS_NETWORK_PRIVATE,
        'network_public': util.env.OS_NETWORK_PUBLIC,
        'script_boot': Transform(
            openstack_worker_script,
            default_script_path=util.env.OS_SCRIPT_BOOT_FILE_PATH,
            user_script_contents=None),
        'script_init': Transform(
            openstack_worker_script,
            default_script_path=util.env.OS_SCRIPT_INIT_FILE_PATH,
            user_script_contents=Property('init.sh')),
        'script_requirements': Transform(
            openstack_worker_script,
            default_script_path=util.env.OS_SCRIPT_REQUIREMENTS_FILE_PATH,
            user_script_contents=Property('requirements.sh')),
        'script_start': Transform(
            openstack_worker_script,
            default_script_path=util.env.OS_SCRIPT_START_FILE_PATH,
            user_script_contents=Property('start.sh')),
        'worker_version': version,
        'redhat_username': util.env.REDHAT_USERNAME,
        'redhat_password': util.env.REDHAT_PASSWORD,
        'redhat_pool': util.env.REDHAT_POOL,
        'redhat_org': util.env.REDHAT_ORG,
        'redhat_activationkey': util.env.REDHAT_ACTIVATIONKEY,
    }

    for i in range(util.env.MAX_OPENSTACK_WORKERS):
        name = 'hw%03d-%s' % (i, util.env.SUFFIX)
        password = util.password_generator()

        params['worker_name'] = name
        params['worker_password'] = password

        workers.append(
            worker.HeatLatentWorker(
                name=name,
                password=password,
                heat_template=template,
                heat_params=dict(params),  # a new copy for each worker
                os_auth_url=util.env.OS_AUTH_URL,
                os_username=util.env.OS_USERNAME,
                os_password=util.env.OS_PASSWORD,
                os_project_domain_id=util.env.OS_PROJECT_DOMAIN_ID,
                os_project_name=util.env.OS_TENANT_NAME,
                os_region_name=util.env.OS_REGION_NAME,
                os_identity_api_version=util.env.OS_IDENTITY_API_VERSION,
                build_wait_timeout=0,  # do not reuse the stack
                keepalive_interval=300))
    return workers
