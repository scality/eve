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

from os.path import abspath, dirname, join

from buildbot.plugins import util, worker
from buildbot.process.properties import Interpolate, Property
from buildbot.worker.local import LocalWorker
from twisted.python.reflect import namedModule


def local_workers():
    workers = []
    for i in range(util.env.MAX_LOCAL_WORKERS):
        worker_ = LocalWorker('lw%03d-%s-%s' % (
            i, util.env.GIT_SLUG, util.env.SUFFIX))
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
                name='dw%03d-%s-%s' % (i, util.env.GIT_SLUG, util.env.SUFFIX),
                password=util.password_generator(),
                master_fqdn=util.env.MASTER_FQDN,
                pb_port=util.env.EXTERNAL_PB_PORT,
                artifacts_prefix=util.env.ARTIFACTS_PREFIX,
                max_memory=util.env.DOCKER_CONTAINER_MAX_MEMORY,
                max_cpus=util.env.DOCKER_CONTAINER_MAX_CPU,
                image=Property('docker_image'),
                keepalive_interval=300,
            ))
    return workers


START_WORKER_SCRIPT = """
echo https://{githost_login}:{githost_pwd}@bitbucket.org \
  >> /home/eve/.git_credentials
echo https://{githost_login}:{githost_pwd}@github.com  \
  >> /home/eve/.git_credentials
chown eve.eve /home/eve/.git_credentials
chmod 600 /home/eve/.git_credentials
sudo -Hu eve git config --global \
  credential.helper 'store --file=/home/eve/.git_credentials'
sudo -Hu eve git config --global \
  url.https://bitbucket.org/.insteadOf git@bitbucket.org:
sudo -Hu eve git config --global \
  url.https://github.com/.insteadOf git@github.com:
sudo -Hu eve buildbot-worker create-worker --umask=022 /home/eve/worker \
"{master_fqdn}:{master_port}" {worker_name} "{worker_password}"
sudo -Hu eve buildbot-worker start /home/eve/worker
"""


def openstack_heat_workers():
    workers = []
    heat_template = open(join(dirname(abspath(__file__)),
                              'single_node_heat_template.yml')).read()

    for i in range(util.env.MAX_OPENSTACK_WORKERS):
        name = 'hw%03d-%s-%s' % (i, util.env.GIT_SLUG, util.env.SUFFIX)
        password = util.password_generator()

        start_worker_script = Interpolate(START_WORKER_SCRIPT.format(
            githost_login=util.env.EVE_GITHOST_LOGIN,
            githost_pwd=util.env.EVE_GITHOST_PWD,
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
                    'image': Property('openstack_image'),
                    'flavor': Property('openstack_flavor'),
                    'key_name': util.env.OS_KEY_NAME,
                    'worker_version': '0.9.7',
                    'worker_init_script': Property('init_script'),
                    'worker_requirements_script': Property(
                        'requirements_script'),
                    'start_worker_script': start_worker_script,
                    'public_network': util.env.OS_NETWORKS
                },
                os_auth_url=util.env.OS_AUTH_URL,
                os_username=util.env.OS_USERNAME,
                os_password=util.env.SECRET_OS_PASSWORD,
                os_project_id=util.env.OS_TENANT_NAME,
                os_region_name=util.env.OS_REGION_NAME,
                build_wait_timeout=0,  # do not reuse the stack
                keepalive_interval=300
            ))
    return workers
